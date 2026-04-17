"""
Daraja M-Pesa API Integration for SalesSmart POS
Handles STK Push, Transaction Status, and Callback processing
"""

import requests
import base64
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from .models import Sale
import logging

logger = logging.getLogger(__name__)


class DarajaAPI:
    """Daraja M-Pesa API Client"""
    
    def __init__(self, business):
        self.business = business
        self.consumer_key = business.daraja_consumer_key
        self.consumer_secret = business.daraja_consumer_secret
        self.passkey = business.daraja_passkey
        self.shortcode = business.daraja_shortcode
        self.initiator_name = business.daraja_initiator_name
        self.callback_url = business.daraja_callback_url
        self.base_url = "https://sandbox.safaricom.co.ke"  # Use sandbox for testing
        self.access_token = None
        
    def get_access_token(self):
        """Get OAuth access token from Daraja"""
        try:
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            if not self.access_token:
                raise Exception("No access token received from Daraja API")
                
            logger.info(f"Successfully obtained Daraja access token for {self.business.name}")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Daraja API request failed: {e}")
            raise Exception(f"Failed to get access token: {e}")
        except Exception as e:
            logger.error(f"Daraja authentication error: {e}")
            raise Exception(f"Authentication failed: {e}")
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push for M-Pesa payment
        
        Args:
            phone_number: Customer phone number (format: 2547XXXXXXXX)
            amount: Amount to charge
            account_reference: Reference for the transaction
            transaction_desc: Description of transaction
        
        Returns:
            dict: Response from Daraja API
        """
        try:
            if not self.access_token:
                self.get_access_token()
            
            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+'):
                phone_number = phone_number[1:]
            
            # Prepare STK Push request
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(
                f"{self.shortcode}{self.passkey}{timestamp}".encode()
            ).decode()
            
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc,
                "CallBackURL": f"{self.callback_url}/mpesa/callback/"
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"STK Push initiated for {phone_number}: {data}")
            
            return {
                "success": True,
                "data": data,
                "checkout_request_id": data.get('CheckoutRequestID'),
                "merchant_request_id": data.get('MerchantRequestID'),
                "response_description": data.get('ResponseDescription')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push request failed: {e}")
            return {
                "success": False,
                "error": f"STK Push failed: {e}"
            }
        except Exception as e:
            logger.error(f"STK Push error: {e}")
            return {
                "success": False,
                "error": f"STK Push error: {e}"
            }
    
    def query_transaction_status(self, checkout_request_id):
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id: The checkout request ID from STK Push
        
        Returns:
            dict: Transaction status response
        """
        try:
            if not self.access_token:
                self.get_access_token()
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(
                f"{self.shortcode}{self.passkey}{timestamp}".encode()
            ).decode()
            
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Transaction status query for {checkout_request_id}: {data}")
            
            return {
                "success": True,
                "data": data,
                "result_code": data.get('ResultCode'),
                "result_desc": data.get('ResultDesc'),
                "status": self._get_transaction_status(data.get('ResultCode'))
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Transaction status query failed: {e}")
            return {
                "success": False,
                "error": f"Status query failed: {e}"
            }
        except Exception as e:
            logger.error(f"Transaction status error: {e}")
            return {
                "success": False,
                "error": f"Status query error: {e}"
            }
    
    def _get_transaction_status(self, result_code):
        """Convert result code to human readable status"""
        if result_code == 0:
            return "Completed"
        elif result_code == 1:
            return "Failed"
        elif result_code == 1032:
            return "Cancelled"
        else:
            return "Pending"


def process_mpesa_callback(callback_data):
    """
    Process M-Pesa callback data
    
    Args:
        callback_data: JSON data from M-Pesa callback
    
    Returns:
        dict: Processing result
    """
    try:
        logger.info(f"Processing M-Pesa callback: {callback_data}")
        
        # Extract callback data
        result_data = callback_data.get('Body', {}).get('stkCallback', {})
        
        if not result_data:
            raise Exception("Invalid callback data structure")
        
        checkout_request_id = result_data.get('CheckoutRequestID')
        result_code = result_data.get('ResultCode')
        result_desc = result_data.get('ResultDesc')
        
        # Find the sale associated with this transaction
        try:
            sale = Sale.objects.get(mpesa_transaction_id=checkout_request_id)
        except Sale.DoesNotExist:
            logger.warning(f"No sale found for checkout request ID: {checkout_request_id}")
            return {
                "success": False,
                "error": "Sale not found"
            }
        
        # Update sale based on transaction result
        if result_code == 0:  # Success
            sale.payment_status = 'Paid'
            sale.notes = f"M-Pesa payment completed successfully. {result_desc}"
            logger.info(f"M-Pesa payment completed for sale {sale.sale_number}")
        else:  # Failed
            sale.payment_status = 'Cancelled'
            sale.notes = f"M-Pesa payment failed: {result_desc}"
            logger.warning(f"M-Pesa payment failed for sale {sale.sale_number}: {result_desc}")
        
        sale.save()
        
        return {
            "success": True,
            "sale_id": sale.id,
            "sale_number": sale.sale_number,
            "payment_status": sale.payment_status,
            "result_code": result_code,
            "result_desc": result_desc
        }
        
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def validate_daraja_settings(business):
    """
    Validate that all required Daraja settings are configured
    
    Args:
        business: Business model instance
    
    Returns:
        dict: Validation result
    """
    required_fields = {
        'daraja_consumer_key': business.daraja_consumer_key,
        'daraja_consumer_secret': business.daraja_consumer_secret,
        'daraja_passkey': business.daraja_passkey,
        'daraja_shortcode': business.daraja_shortcode,
        'daraja_initiator_name': business.daraja_initiator_name,
        'daraja_callback_url': business.daraja_callback_url
    }
    
    missing_fields = [field for field, value in required_fields.items() if not value]
    
    if missing_fields:
        return {
            "valid": False,
            "missing_fields": missing_fields,
            "error": f"Missing required Daraja settings: {', '.join(missing_fields)}"
        }
    
    return {
        "valid": True,
        "message": "Daraja settings are properly configured"
    }
