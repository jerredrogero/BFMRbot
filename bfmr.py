import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BFMRAPI:
    def __init__(self, api_key='e39d9a41c58b', api_secret='b31c02e02ef5aef'):
        self.api_key = api_key
        self.api_secret = api_secret

    def get_active_deals(self, page_size=10):
        try:
            url = 'https://api.bfmr.com/api/v2/deals'
            headers = {
                'API-KEY': self.api_key,
                'API-SECRET': self.api_secret
            }
            params = {
                'page_size': page_size,
                'page_no': 1,
                'exclusive_deals_only': '0'
            }

            response = requests.get(url, headers=headers, params=params)
            # Check status code before processing
            if response.status_code != 200:
                return response
            
            response.raise_for_status()
            deals_data = response.json().get('deals', [])
            
            # Process the deals
            processed_deals = []
            for deal in deals_data:
                retail_price = float(deal.get('retail_price', 0))
                payout_price = float(deal.get('payout_price', 0))
                price_difference = payout_price - retail_price
                
                # Get first item's URL if available
                product_url = ''
                items = deal.get('items', [])
                if items and items[0].get('retailer_links'):
                    product_url = items[0]['retailer_links'][0].get('url', '')

                processed_deal = {
                    'deal_id': deal.get('deal_id'),
                    'title': deal.get('title'),
                    'retail_price': retail_price,
                    'payout_price': payout_price,
                    'price_difference': price_difference,
                    'product_url': product_url,
                    'items': items,
                    'retailers': deal.get('retailers'),
                    'deal_code': deal.get('deal_code')
                }
                processed_deals.append(processed_deal)
            
            return {'deals': processed_deals, 'status_code': response.status_code}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"BFMR API request failed: {e}")
            raise

    def commit_to_deal(self, deal_id: str, item_id: str, item_qty: str):
        """Commit to a deal using the BFMR API"""
        try:
            url = 'https://api.bfmr.com/api/v2/deals/reserve'
            headers = {
                'API-KEY': self.api_key,
                'API-SECRET': self.api_secret,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'deal_id': deal_id,
                'item_id': item_id,
                'item_qty': item_qty
            }
            
            logger.info(f"Making reservation request: {data}")
            response = requests.post(url, headers=headers, data=data)
            logger.info(f"BFMR API response: {response.text}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Quantity reserved successfully"
                }
            else:
                error_message = response.json().get('message', 'Unknown error occurred')
                return {
                    "success": False,
                    "error": error_message
                }
        except Exception as e:
            logger.error(f"Error in commit_to_deal: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    bfmr = BFMRAPI()
    
    # Get active deals
    deals = bfmr.get_active_deals(page_size=10)
    if deals and deals.get('deals'):
        logger.info(f"Found {len(deals['deals'])} active deals")
        
        # Print each deal's details
        for deal in deals['deals']:
            print("\n" + "="*80)
            print(f"Title: {deal.get('title')}")
            print(f"Retail Price: ${deal.get('retail_price', 0):.2f}")
            print(f"Payout Price: ${deal.get('payout_price', 0):.2f}")
            print(f"Retailer: {deal.get('retailers')}")
            print(f"Type: {deal.get('retail_type')}")
            print(f"Closing at: {deal.get('closing_at')}")
            print(f"Deal ID: {deal.get('deal_id')}")
            
            # Calculate profit
            profit = float(deal.get('payout_price', 0)) - float(deal.get('retail_price', 0))
            print(f"Potential Profit: ${profit:.2f}")
            
            if profit > 0:
                profit_percent = (profit / float(deal.get('retail_price', 1))) * 100
                print(f"Profit Percentage: {profit_percent:.1f}%")
            
            if deal.get('is_exclusive_deal'):
                print("*** EXCLUSIVE DEAL ***")
    else:
        logger.error("No deals found or error getting deals")
