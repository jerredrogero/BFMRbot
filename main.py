import requests
import logging
import time
from pprint import pprint

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_all_deals(api_key='e39d9a41c58b', api_secret='b31c02e02ef5aef'):
    url = 'https://api.bfmr.com/api/v2/deals/'
    headers = {
        'API-KEY': api_key,
        'API-SECRET': api_secret
    }
    
    params = {
        'page_size': 10
    }

    try:
        logger.info("Fetching deals from BFMR...")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            deals = data.get('deals', {})
            if isinstance(deals, dict):
                deals = [deals]
            logger.info(f"Found {len(deals)} deals")
            return deals
        else:
            logger.error(f"Error {response.status_code}: {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        return []

def calculate_profit(deal):
    retail = float(deal.get('retail_price', 0))
    payout = float(deal.get('payout_price', 0))
    return payout - retail

def main():
    deals = get_all_deals()
    
    if not deals:
        print("No deals available")
        return
        
    # Sort deals by profit
    deals.sort(key=calculate_profit, reverse=True)
        
    print(f"\nFound {len(deals)} deals (sorted by profit):")
    for deal in deals:
        print("\n" + "="*50)
        print(f"Title: {deal.get('title')}")
        
        retail = float(deal.get('retail_price', 0))
        payout = float(deal.get('payout_price', 0))
        profit = payout - retail
        profit_percent = (profit / retail * 100) if retail > 0 else 0
        
        print(f"Retail Price: ${retail:.2f}")
        print(f"Payout Price: ${payout:.2f}")
        print(f"Profit: ${profit:.2f} ({profit_percent:.1f}%)")
        print(f"Deal ID: {deal.get('deal_id')}")

if __name__ == "__main__":
    main()