"""Review donor submissions and send persistent in-app donor notifications."""
import json
from datetime import datetime
from pathlib import Path

from app.auth.account_manager import AccountManager

NOTIFICATION_PATH = Path('assets/donor_notifications.json')


def list_donations(manager):
    result = []
    for donor in manager._accounts.get('Donor', []):
        for record in donor.get('_donation_rec', []):
            for index, item in enumerate(record.get('donation', [])):
                result.append({
                    'donor_id': donor['_account_number'],
                    'donor_name': donor.get('_name', 'Unknown'),
                    'donation_id': record.get('id'),
                    'item_index': index,
                    'item': item,
                })
    return result


def review_donation(manager, donor_id, donation_id, item_index, decision,
                    notification_path=NOTIFICATION_PATH):
    if decision not in ('Accepted', 'Rejected'):
        raise ValueError('Decision must be Accepted or Rejected.')
    donor = manager.find_account(donor_id, 'Donor')
    if donor is None:
        raise ValueError('Donor not found.')
    for record in donor.get('_donation_rec', []):
        if str(record.get('id')) != str(donation_id):
            continue
        items = record.get('donation', [])
        if not 0 <= item_index < len(items):
            raise ValueError('Donation item not found.')
        item = items[item_index]
        if item.get('status') != 'Pending':
            raise ValueError('Only pending donations can be reviewed.')
        # Save notification first so an invalid notification file cannot silently
        # leave an approved donation without its corresponding donor alert.
        path = Path(notification_path)
        if path.exists():
            with path.open('r', encoding='utf-8') as f:
                notifications = json.load(f)
            if not isinstance(notifications, list):
                raise ValueError('Notification file must contain a list.')
        else:
            notifications = []
        notifications.append({
            'donor_id': str(donor_id),
            'message': f'Donation {donation_id} has been {decision.lower()} by Food Staff.',
            'timestamp': datetime.now().isoformat(),
            'read': False,
        })
        # Existing AccountManager is the source of truth for donation status.
        item['status'] = decision
        try:
            manager.save_data()
        except Exception:
            item['status'] = 'Pending'
            raise
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as f:
            json.dump(notifications, f, indent=4)
        return item
    raise ValueError('Donation not found.')
