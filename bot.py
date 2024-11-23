from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
import logging
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from bfmr import BFMRAPI

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# States for the setup conversation
APIKEY, APISECRET = range(2)

# Store user credentials (in memory - would use database in production)
user_credentials = {}

class UserBFMR:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def get_active_deals(self, page_size=10):
        """Get active deals from BFMR API"""
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
        response.raise_for_status()
        return response.json()

    def commit_to_deal(self, deal_id: str, item_id: str, item_qty: str):
        """Commit to a deal using the BFMR API"""
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

    def test_credentials(self):
        """Test if API credentials are valid"""
        try:
            # Just try to fetch one deal to test credentials
            self.get_active_deals(page_size=1)
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API credentials")
            raise
        except Exception as e:
            raise ValueError(f"Error testing credentials: {str(e)}")

# Helper functions
def get_user_bfmr(user_id: str) -> UserBFMR:
    """Get a BFMR API instance for the user"""
    if str(user_id) not in user_credentials:
        return None
    
    creds = user_credentials[str(user_id)]
    return UserBFMR(api_key=creds['api_key'], api_secret=creds['api_secret'])

async def check_credentials(update: Update) -> bool:
    """Check if user has configured API credentials"""
    if str(update.effective_user.id) not in user_credentials:
        await update.message.reply_text(
            "⚠️ Please configure your API credentials first using /setup"
        )
        return False
    return True

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if str(update.effective_user.id) not in user_credentials:
        text = (
            "👋 Welcome to the BFMR Deal Bot by BuyingGroupPro!\n\n"
            "Before we begin, you'll need to set up your BFMR API credentials.\n"
            "Use /setup to configure your API key and secret.\n\n"
            "🔗 Visit [BuyingGroupPro.com](https://buyingrouppro.com) for more tools and resources!"
        )
        keyboard = [[InlineKeyboardButton("🌐 Visit BuyingGroupPro.com", url="https://buyingrouppro.com")]]
    else:
        text = (
            "👋 Welcome to the BFMR Deal Bot by BuyingGroupPro!\n\n"
            "🌟 *Features*:\n"
            "• View all active BFMR deals at once (/viewall)\n"
            "• Browse deals one at a time (/deals)\n"
            "• Filter at or above retail priced deals (/profitable)\n"
            "• Easy deal commitment\n\n"
            "🔗 Visit [BuyingGroupPro.com](https://buyingrouppro.com) for more tools and resources!"
        )
        keyboard = [
            [InlineKeyboardButton("📦 View All Deals", callback_data="view_all")],
            [InlineKeyboardButton("💰 Profitable Deals Only", callback_data="view_profitable")],
            [InlineKeyboardButton("🌐 Visit BuyingGroupPro.com", url="https://buyingrouppro.com")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup, disable_web_page_preview=True)

# Setup process handlers
async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the setup process"""
    await update.message.reply_text(
        "🔑 Let's configure your BFMR API credentials.\n\n"
        "Please enter your BFMR API Public Key:\n"
        "(or use /cancel to cancel setup)",
        reply_markup=ForceReply(selective=True)
    )
    return APIKEY

async def api_key_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API key input"""
    # Delete the message containing the API key for security
    await update.message.delete()
    
    context.user_data['api_key'] = update.message.text
    await update.message.reply_text(
        "Great! Now please enter your BFMR API Secret:\n"
        "(or use /cancel to cancel setup)",
        reply_markup=ForceReply(selective=True)
    )
    return APISECRET

async def api_secret_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API secret input and complete setup"""
    # Delete the message containing the API secret for security
    await update.message.delete()
    
    api_key = context.user_data.get('api_key')
    api_secret = update.message.text
    
    # Test the credentials
    try:
        bfmr = UserBFMR(api_key=api_key, api_secret=api_secret)
        
        # First test the credentials
        try:
            bfmr.test_credentials()
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Invalid API credentials: {str(e)}\n"
                "Please check your credentials and try /setup again."
            )
            return ConversationHandler.END
        
        # If credentials are valid, store them
        user_credentials[str(update.effective_user.id)] = {
            'api_key': api_key,
            'api_secret': api_secret,
            'setup_date': datetime.now().isoformat()
        }
        
        await update.message.reply_text(
            "✅ API credentials verified and saved successfully!\n\n"
            "You can now use the following commands:\n"
            "/deals - View all available deals\n"
            "/profitable - View all deals at or above retail\n"
            "/viewall - View all deals at once\n"
            "/search [term] - Search for specific deals\n"
            "/help - Show all available commands"
        )
            
    except Exception as e:
        logger.error(f"API credential verification failed: {str(e)}")
        error_message = str(e)
        if "401" in error_message:
            error_message = "Invalid API credentials. Please check your API key and secret."
        elif "404" in error_message:
            error_message = "API endpoint not found. Please check if the API is available."
        
        await update.message.reply_text(
            f"❌ Failed to verify API credentials.\n"
            f"Error: {error_message}\n\n"
            "Please try /setup again with correct credentials."
        )
    
    # Clear sensitive data from context
    if 'api_key' in context.user_data:
        del context.user_data['api_key']
    
    return ConversationHandler.END

async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the setup process"""
    # Clear any stored credentials
    if 'api_key' in context.user_data:
        del context.user_data['api_key']
    
    await update.message.reply_text(
        "❌ Setup cancelled.\n"
        "Use /setup to try again when you're ready."
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available commands"""
    help_text = (
        "🤖 *BFMR Deal Bot by BuyingGroupPro.com*\n\n"
        "*Available Commands:*\n"
        "/start - Start the bot\n"
        "/setup - Configure your API credentials\n"
        "/viewall - View all deals at once\n"
        "/deals - Browse deals one at a time\n"
        "/profitable - View profitable deals only\n"
        "/search [term] - Search for specific deals\n"
        "/help - Show this help message\n\n"
        "💡 *Pro Tips:*\n"
        "• Use /viewall to see all available deals\n"
        "• Try /search Macbook to find all Macbook deals\n\n"
        "🔗 Visit [BuyingGroupPro.com](https://buyingrouppro.com) for more reselling tools!"
    )
    
    keyboard = [[InlineKeyboardButton("🌐 Visit BuyingGroupPro.com", url="https://buyingrouppro.com")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup, disable_web_page_preview=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        # Send error message to user
        error_message = (
            "❌ An error occurred while processing your request.\n"
            "Please try again later or contact support if the issue persists."
        )
        if update.effective_message:
            await update.effective_message.reply_text(error_message)
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

async def send_deal_message(update: Update, deal: dict, is_reply: bool = False, show_navigation: bool = False):
    """Send a formatted deal message"""
    try:
        # Format deal message
        deal_id = deal.get('deal_id', '')
        text = (
            f"🏷️ *{deal.get('title', '')}*\n\n"
            f"💰 Retail: ${deal.get('retail_price', 0)}\n"
            f"💵 Payout: ${deal.get('payout_price', 0)}\n"
            f"📈 Profit: ${float(deal.get('payout_price', 0)) - float(deal.get('retail_price', 0)):.2f}\n"
            f"🏪 Retailer: {deal.get('retailers', '')}\n"
            f"📦 Type: {deal.get('retail_type', '')}\n"
            f"⏰ Closing: {deal.get('closing_at', '')}\n"
        )
        
        # Add footer
        text += "\n🤖 *Powered by [BuyingGroupPro.com](https://buyinggrouppro.com)*"
        
        # Create buttons for each item
        keyboard = []
        for item in deal.get('items', []):
            name_parts = item.get('name', '').split(' - ')
            color = item.get('color', '')
            button_text = f"Commit: {name_parts[0]} - {color}"
            callback_data = f"select_{deal_id}_{item['id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add navigation buttons only if show_navigation is True
        if show_navigation:
            keyboard.append([
                InlineKeyboardButton("⬅️ Previous", callback_data="prev_deal"),
                InlineKeyboardButton("Next ➡️", callback_data="next_deal")
            ])
        
        # Add website button
        keyboard.append([InlineKeyboardButton("🌐 Visit BuyingGroupPro.com", url="https://buyinggrouppro.com")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if isinstance(update, Update):
            return await update.message.reply_text(
                text, 
                parse_mode='Markdown', 
                reply_markup=reply_markup, 
                disable_web_page_preview=True
            )
        else:
            return await update.edit_text(
                text, 
                parse_mode='Markdown', 
                reply_markup=reply_markup, 
                disable_web_page_preview=True
            )
            
    except Exception as e:
        logger.error(f"Error sending deal message: {e}")
        if isinstance(update, Update):
            await update.message.reply_text("❌ Error displaying deal. Please try again later.")

async def deals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available deals"""
    if not await check_credentials(update):
        return
        
    message = await update.message.reply_text("🔍 Fetching deals...")
    bfmr = get_user_bfmr(str(update.effective_user.id))
    
    try:
        response = bfmr.get_active_deals(page_size=50)
        
        if response.status_code != 200:
            error_msg = "❌ An error occurred while fetching deals."
            if response.status_code == 500:
                error_msg = "⚠️ BFMR API is temporarily unavailable. Please try again in a few minutes."
            elif response.status_code == 401:
                error_msg = "❌ Invalid API credentials. Please use /setup to reconfigure."
            elif response.status_code == 403:
                error_msg = "❌ Access forbidden. Please check your API permissions."
                
            logger.error(f"BFMR API error: {response.status_code} - {response.text}")
            await message.edit_text(error_msg)
            return
            
        data = response.json()
        deals = data.get('deals', [])
        
        if not deals:
            await message.edit_text("No deals available at the moment.")
            return
            
        # Store deals in context
        context.user_data['current_deals'] = deals
        context.user_data['current_deal_index'] = 0
        
        # Send first deal
        await message.delete()
        await send_deal_message(update, deals[0], show_navigation=True)
        
    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        await message.edit_text("❌ An unexpected error occurred. Please try again later.")

async def profitable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profitable deals only"""
    if not await check_credentials(update):
        return
        
    message = await update.message.reply_text("🔍 Fetching profitable deals...")
    bfmr = get_user_bfmr(str(update.effective_user.id))
    
    try:
        response = bfmr.get_active_deals(page_size=50)
        all_deals = response.get('deals', [])
        
        # Filter for profitable deals by calculating profit from retail and payout prices
        profitable_deals = [
            deal for deal in all_deals 
            if float(deal.get('payout_price', 0)) > float(deal.get('retail_price', 0))
        ]
        
        if not profitable_deals:
            await message.edit_text("No profitable deals available at the moment.")
            return
        
        # Sort by profit margin (highest first)
        profitable_deals.sort(
            key=lambda x: float(x.get('payout_price', 0)) - float(x.get('retail_price', 0)), 
            reverse=True
        )
        
        await message.edit_text(f"Found {len(profitable_deals)} profitable deals")
        
        # Send each profitable deal
        for deal in profitable_deals:
            await send_deal_message(update, deal, is_reply=True)
            
    except Exception as e:
        logger.error(f"Error fetching profitable deals: {e}")
        await message.edit_text("❌ Error fetching profitable deals. Please try again later.")

async def viewall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all deals at once"""
    if not await check_credentials(update):
        return
        
    message = await update.message.reply_text("🔍 Fetching all deals...")
    bfmr = get_user_bfmr(str(update.effective_user.id))
    
    try:
        response = bfmr.get_active_deals(page_size=50)
        deals = response.get('deals', [])
        
        if not deals:
            await message.edit_text("No deals available at the moment.")
            return
            
        await message.edit_text(f"Found {len(deals)} deals")
        
        # Send each deal as a separate message
        for deal in deals:
            keyboard = []
            # Add commit buttons for each item
            for item in deal.get('items', []):
                name_parts = item.get('name', '').split(' - ')
                color = item.get('color', '')
                button_text = f"Commit: {name_parts[0]} - {color}"
                callback_data = f"select_{deal.get('deal_id')}_{item['id']}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Add website button
            keyboard.append([InlineKeyboardButton("🌐 Visit BuyingGroupPro.com", url="https://buyingrouppro.com")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_deal_message(update, deal, is_reply=True)
            
    except Exception as e:
        logger.error(f"Error fetching all deals: {e}")
        await message.edit_text("❌ Error fetching deals. Please try again later.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data.startswith('select_'):
            # Handle item selection
            _, deal_id, item_id = query.data.split('_', 2)
            context.user_data['pending_commit'] = {
                'deal_id': deal_id,
                'item_id': item_id
            }
            await query.message.reply_text(
                "How many units would you like to commit to? (Enter a number)",
                reply_markup=ForceReply(selective=True)
            )
        
        elif query.data == 'view_profitable':
            await profitable_command(query, context)
            
        elif query.data == 'view_all':
            await viewall_command(query, context)
            
        elif query.data in ['prev_deal', 'next_deal']:
            # Handle deal navigation
            deals = context.user_data.get('current_deals', [])
            current_index = context.user_data.get('current_deal_index', 0)
            
            if query.data == 'next_deal':
                new_index = (current_index + 1) % len(deals)
            else:
                new_index = (current_index - 1) % len(deals)
            
            context.user_data['current_deal_index'] = new_index
            await send_deal_message(query.message, deals[new_index], show_navigation=True)
            
    except Exception as e:
        logger.error(f"Error in button callback: {e}")
        await query.message.reply_text("❌ Error processing selection. Please try again later.")

async def handle_quantity_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quantity response for deal commitment"""
    try:
        if 'pending_commit' not in context.user_data:
            return

        # Get the quantity
        qty = update.message.text.strip()
        if not qty.isdigit() or int(qty) < 1:
            await update.message.reply_text("❌ Please enter a valid number greater than 0.")
            return

        # Get the stored deal and item IDs
        deal_id = context.user_data['pending_commit']['deal_id']
        item_id = context.user_data['pending_commit']['item_id']
        
        # Debug log to see the exact values
        logger.info(f"Raw deal_id: {deal_id}")
        logger.info(f"Raw item_id: {item_id}")
        
        # Clean the IDs (remove any potential URL encoding or special characters)
        deal_id = deal_id.strip()
        item_id = item_id.strip()
        
        logger.info(f"Attempting to commit with cleaned IDs: deal_id={deal_id}, item_id={item_id}, qty={qty}")
        
        # Commit to the deal
        bfmr = get_user_bfmr(str(update.effective_user.id))
        if not bfmr:
            await update.message.reply_text("❌ Please configure your API credentials first using /setup")
            return

        # Make the API request with cleaned IDs
        result = bfmr.commit_to_deal(deal_id=deal_id, item_id=item_id, item_qty=qty)
        
        # Debug log the full API response
        logger.info(f"Full API Response: {result}")
        
        api_message = result.get('error', '').lower()
        
        if result.get('success'):
            await update.message.reply_text(
                f"✅ Successfully committed to deal!\n"
                f"Quantity: {qty}\n"
                f"Please check your BFMR dashboard for next steps."
            )
        else:
            # Handle specific error messages
            if "not available" in api_message:
                error_msg = "❌ This deal is no longer available."
            elif "reservations is closed" in api_message:
                error_msg = "❌ This deal is currently closed for reservations."
            elif "already reserved" in api_message:
                error_msg = "❌ You have already reserved this deal."
            elif "limit exceeded" in api_message:
                error_msg = "❌ Reservation limit exceeded for this deal."
            elif "quantity reserved failed" in api_message:
                error_msg = "❌ Unable to reserve the requested quantity. No units available."
            else:
                error_msg = f"❌ Unable to commit to deal: {result.get('error', 'Unknown error')}"
            
            await update.message.reply_text(error_msg)
            
        # Clear the pending commit
        del context.user_data['pending_commit']
        
    except Exception as e:
        logger.error(f"Error handling quantity: {e}")
        await update.message.reply_text("❌ Error processing commitment. Please try again later.")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for deals by keyword"""
    if not await check_credentials(update):
        return
        
    # Check if search term was provided
    if not context.args:
        await update.message.reply_text(
            "Please provide a search term.\n"
            "Example: `/search nintendo`", 
            parse_mode='Markdown'
        )
        return
        
    search_term = ' '.join(context.args).lower()
    message = await update.message.reply_text(f"🔍 Searching for deals matching: *{search_term}*...", parse_mode='Markdown')
    bfmr = get_user_bfmr(str(update.effective_user.id))
    
    try:
        response = bfmr.get_active_deals(page_size=50)
        all_deals = response.get('deals', [])
        
        # Search in deal titles and descriptions
        matching_deals = [
            deal for deal in all_deals 
            if search_term in deal.get('title', '').lower() 
            or search_term in deal.get('description', '').lower()
            or any(search_term in item.get('name', '').lower() for item in deal.get('items', []))
        ]
        
        if not matching_deals:
            await message.edit_text(f"No deals found matching: *{search_term}*", parse_mode='Markdown')
            return
        
        await message.edit_text(f"Found {len(matching_deals)} deals matching: *{search_term}*", parse_mode='Markdown')
        
        # Send each matching deal
        for deal in matching_deals:
            await send_deal_message(update, deal, is_reply=True)
            
    except Exception as e:
        logger.error(f"Error searching deals: {e}")
        await message.edit_text("❌ Error searching deals. Please try again later.")

def main():
    """Start the bot"""
    app = Application.builder().token(TOKEN).build()
    
    # Setup conversation handler
    setup_handler = ConversationHandler(
        entry_points=[CommandHandler('setup', setup_command)],
        states={
            APIKEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, api_key_received)],
            APISECRET: [MessageHandler(filters.TEXT & ~filters.COMMAND, api_secret_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel_setup)]
    )
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(setup_handler)
    app.add_handler(CommandHandler("deals", deals_command))
    app.add_handler(CommandHandler("profitable", profitable_command))
    app.add_handler(CommandHandler("viewall", viewall_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_quantity_response))
    
    app.add_error_handler(error_handler)
    
    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
