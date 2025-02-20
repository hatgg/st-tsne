from .types import CardInfo
import streamlit as st


def render_card(card: CardInfo):
    # Build the HTML string to match your TS component's styling
    card_html = f"""
    <div style="border: 2px solid #D1D5DB; padding: 16px; border-radius: 8px; background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 16px;">
        <!-- Top Card Info -->
        <div style="margin-bottom: 8px; font-weight: 500; color: #9CA3AF;">
            Element: {card.element}
        </div>
        <div style="margin-bottom: 4px; color: #9CA3AF;">
            Legality: {card.legality}
        </div>
        <div style="margin-bottom: 8px; color: #9CA3AF;">
            View Type: {card.viewType}
        </div>
        <!-- Effects Section -->
        <div style="color: #4B5563; font-size: 14px;">
            <div style="font-weight: 600; margin-bottom: 4px;">Effects:</div>
            <ul style="list-style-type: disc; padding-left: 16px; margin: 0;">
    """
    for effect in card.effects:
        if effect is None:
            card_html += '<li><em style="color: #9CA3AF;">None</em></li>'
        else:
            card_html += f"<li>{effect.type} ({effect.target}): {effect.value}</li>"
    card_html += """
            </ul>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
