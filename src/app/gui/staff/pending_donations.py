"""Food Staff page for reviewing incoming donor donations."""
import streamlit as st

from app.auth.account_manager import AccountManager
from app.core.donation_review import list_donations, review_donation
from app.gui.shared.toolbar import require_role
from app.users.user import UserAccess


def show_pending_donations():
    require_role(UserAccess.STAFF)
    st.title('Pending Donations')
    st.caption('Review donations registered by Donors. Accepted donations are not automatically added to inventory.')

    manager = AccountManager()
    donations = list_donations(manager)
    pending = [d for d in donations if d['item'].get('status') == 'Pending']
    st.metric('Pending Donations', len(pending))

    if not pending:
        st.info('No pending donations.')

    for donation in pending:
        item = donation['item']
        donor_id = donation['donor_id']
        donation_id = donation['donation_id']
        item_index = donation['item_index']
        with st.expander(f"Donation {donation_id} — {item.get('food_name', 'Food')} ({donation['donor_name']})"):
            st.write(f"Donor: {donation['donor_name']}")
            st.write(f"Food: {item.get('food_name', '-')}")
            st.write(f"Quantity: {item.get('quantity', '-')} {item.get('unit', '')}")
            st.write(f"Category: {item.get('category', '-')}")
            st.write(f"Dietary tags: {', '.join(item.get('food_tag', [])) or 'None'}")
            st.write(f"Expiry date: {item.get('expiry_date', '-')}")
            st.write(f"Drop-off: {item.get('drop_off_date', '-')} at {item.get('drop_off_time', '-')}")
            left, right = st.columns(2)
            key = f'{donor_id}_{donation_id}_{item_index}'
            if left.button('Accept', key='accept_' + key):
                try:
                    review_donation(manager, donor_id, donation_id, item_index, 'Accepted')
                    st.session_state['donation_review_message'] = f'Donation {donation_id} accepted.'
                    st.rerun()
                except (ValueError, OSError) as error:
                    st.error(str(error))
            if right.button('Reject', key='reject_' + key):
                try:
                    review_donation(manager, donor_id, donation_id, item_index, 'Rejected')
                    st.session_state['donation_review_message'] = f'Donation {donation_id} rejected.'
                    st.rerun()
                except (ValueError, OSError) as error:
                    st.error(str(error))

    message = st.session_state.pop('donation_review_message', None)
    if message:
        st.success(message)

    st.subheader('Reviewed Donations')
    reviewed = [d for d in donations if d['item'].get('status') in ('Accepted', 'Rejected')]
    if reviewed:
        st.dataframe([{
            'Donation ID': d['donation_id'],
            'Donor': d['donor_name'],
            'Food': d['item'].get('food_name', '-'),
            'Status': d['item'].get('status'),
        } for d in reviewed], hide_index=True, use_container_width=True)
    else:
        st.info('No reviewed donations yet.')


if __name__ == '__main__':
    show_pending_donations()
