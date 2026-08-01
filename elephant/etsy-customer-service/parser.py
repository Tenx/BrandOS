#!/usr/bin/env python3
"""
Etsy Customer Service Helper
Utility functions for parsing Etsy message data from opencli extracts
"""

import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EtsyMessage:
    """Represents an Etsy message/conversation"""
    conversation_id: str
    conversation_url: str
    buyer_name: str
    buyer_avatar: str
    message_preview: str
    time_received: str
    is_unread: bool
    is_first_time_buyer: bool
    is_order_help: bool
    order_number: Optional[str] = None
    product_title: Optional[str] = None
    product_url: Optional[str] = None
    product_price: Optional[str] = None


@dataclass
class ConversationThread:
    """Represents a full conversation with history"""
    conversation_id: str
    buyer_name: str
    buyer_profile_url: str
    messages: List[Dict[str, str]]  # List of {sender, text, time}
    order_info: Optional[Dict] = None
    product_info: Optional[Dict] = None
    labels: List[str] = None


def parse_message_list(markdown: str) -> List[EtsyMessage]:
    """
    Parse opencli extract output from Etsy Messages inbox
    Returns list of EtsyMessage objects
    """
    messages = []

    # Pattern to match message entries
    # Example: "Select this conversation with Sarah Weakley from 8 hours ago"
    pattern = r'Select this conversation with (.+?) from (.+?)\n\n\[(.+?)\n\n.+?\n\n### (.+?)\n\n### (.+?)\n\n.*?\n\n\*\*(.+?)\*\*\n\n\]\(/messages/(\d+)\)'

    matches = re.finditer(pattern, markdown, re.DOTALL)

    for match in matches:
        buyer_name = match.group(1)
        time_received = match.group(2)
        status = match.group(3)  # "unread message" or "read message"
        message_preview = match.group(5)
        context = match.group(6)
        conversation_id = match.group(7)

        is_unread = "unread" in status
        is_first_time_buyer = "First message from potential buyer" in context
        is_order_help = "Help request" in context

        message = EtsyMessage(
            conversation_id=conversation_id,
            conversation_url=f"/messages/{conversation_id}",
            buyer_name=buyer_name,
            buyer_avatar="",  # Can be extracted from img src if needed
            message_preview=message_preview,
            time_received=time_received,
            is_unread=is_unread,
            is_first_time_buyer=is_first_time_buyer,
            is_order_help=is_order_help
        )

        messages.append(message)

    return messages


def parse_conversation(markdown: str) -> ConversationThread:
    """
    Parse opencli extract output from a single conversation
    Returns ConversationThread with full history
    """
    # Extract buyer name
    buyer_match = re.search(r'!\[(.+?)\]\(https://i\.etsystatic\.com/.+?\)\n\n(.+?)\n', markdown)
    buyer_name = buyer_match.group(2) if buyer_match else "Unknown"

    # Extract buyer profile URL
    profile_match = re.search(r'\[(.+?)\]\((https://www\.etsy\.com/people/.+?)\)', markdown)
    buyer_profile_url = profile_match.group(2) if profile_match else ""

    # Extract conversation ID from URL
    conv_id_match = re.search(r'https://www\.etsy\.com/messages/(\d+)', markdown)
    conversation_id = conv_id_match.group(1) if conv_id_match else ""

    # Extract messages
    messages = []
    message_pattern = r'Message:(.+?)\n\n(.+?)\n'
    for match in re.finditer(message_pattern, markdown, re.DOTALL):
        text = match.group(1).strip()
        time = match.group(2).strip()
        messages.append({
            "sender": "buyer",  # Default to buyer; can be refined
            "text": text,
            "time": time
        })

    # Extract order info if present
    order_info = None
    order_match = re.search(r'# Ordered (.+?)\n\n\[#(\d+)', markdown)
    if order_match:
        order_date = order_match.group(1)
        order_number = order_match.group(2)

        # Extract shipping info
        ship_match = re.search(r'## Ship in (.+?)\n\nEstimated delivery: (.+?)\n', markdown)
        ship_days = ship_match.group(1) if ship_match else ""
        delivery_est = ship_match.group(2) if ship_match else ""

        order_info = {
            "order_number": order_number,
            "order_date": order_date,
            "ship_in": ship_days,
            "estimated_delivery": delivery_est
        }

    # Extract product info
    product_info = None
    product_match = re.search(r'\[!\[\]\((.+?)\)\n\n    (.+?)\n\n    \$(.+?)\n', markdown)
    if product_match:
        product_info = {
            "image": product_match.group(1),
            "title": product_match.group(2),
            "price": product_match.group(3)
        }

    # Extract labels
    labels = []
    labels_match = re.search(r'### Labels\n\n(.+?)(?=\n\n###|\Z)', markdown, re.DOTALL)
    if labels_match:
        labels_text = labels_match.group(1)
        if "No labels added" not in labels_text:
            labels = [l.strip() for l in labels_text.split('\n') if l.strip()]

    return ConversationThread(
        conversation_id=conversation_id,
        buyer_name=buyer_name,
        buyer_profile_url=buyer_profile_url,
        messages=messages,
        order_info=order_info,
        product_info=product_info,
        labels=labels
    )


def categorize_message(message_text: str, order_info: Optional[Dict] = None) -> str:
    """
    Categorize message type based on content
    Returns: 'sizing_inquiry', 'refund_request', 'shipping_concern', 'order_modification', 'general_inquiry'
    """
    text_lower = message_text.lower()

    # Sizing inquiry patterns
    sizing_keywords = ['size', 'fit', 'measurement', 'bust', 'waist', 'hip', 'small', 'medium', 'large']
    if any(kw in text_lower for kw in sizing_keywords):
        return 'sizing_inquiry'

    # Refund/cancellation patterns
    refund_keywords = ['refund', 'cancel', 'return', "change my mind", 'worried on timing']
    if any(kw in text_lower for kw in refund_keywords):
        return 'refund_request'

    # Shipping concern patterns
    shipping_keywords = ['tracking', 'delivery', 'shipped', 'when will', 'customs', 'delayed']
    if any(kw in text_lower for kw in shipping_keywords):
        return 'shipping_concern'

    # Order modification patterns
    modification_keywords = ['change', 'modify', 'different color', 'add', 'remove']
    if any(kw in text_lower for kw in modification_keywords):
        return 'order_modification'

    return 'general_inquiry'


def format_reply_draft(
    buyer_name: str,
    message_type: str,
    draft_text: str,
    conversation_url: str
) -> str:
    """Format a reply draft for user approval"""
    return f"""
---
## Reply Draft for {buyer_name}

**Message Type**: {message_type}
**Conversation**: https://www.etsy.com{conversation_url}

**Proposed Reply**:
{draft_text}

---
"""


if __name__ == "__main__":
    # Test parsing
    sample_markdown = """
Select this conversation with Sarah Weakley from 8 hours ago

[unread message

![Sarah Weakley](https://i.etsystatic.com/iusa/743bfa/30769576/iusa_75x75.30769576_oonc.jpg?version=0)

### Sarah Weakley

### Hi, I am interested in knowing more about the crochet cream tank. I am size 6-8 but bust is a 32/34 DD and I'm 5"1. I am not sure if I would be a S or M. Thanks!

**First message from potential buyer**

**8 hours ago**


](/messages/1683114213)
    """

    messages = parse_message_list(sample_markdown)
    for msg in messages:
        print(f"Buyer: {msg.buyer_name}")
        print(f"Type: {categorize_message(msg.message_preview)}")
        print(f"Unread: {msg.is_unread}")
        print()
