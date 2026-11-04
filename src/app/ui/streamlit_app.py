"""Streamlit presentation; calculations and data access remain in services."""
from datetime import date
from decimal import Decimal
from html import escape
from pathlib import Path

import logging
import os
import streamlit as st

from src.api.bnm_client import BnmClient
from src.api.bnm_provider import BnmRateProvider
from src.cache.rate_cache import RateCache
from src.config.settings import DEFAULT_CACHE_FILE, SOURCE_NAME, SUPPORTED_CURRENCIES
from src.domain.conversion import CurrencyConverter, CurrencyUnavailableError, ExchangeRateUnavailableError
from src.domain.models import ConversionRequest, ConversionResult, RateSnapshot
from src.domain.validation import validate_amount

CURRENCY_NAMES = {
    "MDL": "MDL — Moldovan Leu", "EUR": "EUR — Euro", "USD": "USD — US Dollar",
    "RON": "RON — Romanian Leu", "GBP": "GBP — British Pound", "UAH": "UAH — Ukrainian Hryvnia",
}


def _inject_custom_css() -> None:
    css = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def get_converter() -> CurrencyConverter:
    """Composition root and a seam for deterministic UI tests."""
    test_fixture = os.environ.get("CONVERTER_TEST_FIXTURE")
    if test_fixture:
        from src.parsing.xml_parser import parse_bnm_xml

        xml_text = Path(test_fixture).read_text(encoding="utf-8")
        snapshot = parse_bnm_xml(xml_text)

        class StaticFixtureProvider:
            def get_rates(self, target_date: date) -> RateSnapshot | None:
                return snapshot

        return CurrencyConverter(rate_provider=StaticFixtureProvider())

    test_offline = os.environ.get("CONVERTER_TEST_OFFLINE_CACHE")
    if test_offline:
        class FailingTestProvider:
            def get_rates(self, target_date: date) -> RateSnapshot | None:
                raise ConnectionError("Simulated offline mode")

        cache = RateCache(Path(test_offline))
        return CurrencyConverter(rate_provider=FailingTestProvider(), cache=cache)

    cache = RateCache(DEFAULT_CACHE_FILE)
    provider = BnmRateProvider(client=BnmClient(), cache=cache)
    return CurrencyConverter(rate_provider=provider, cache=cache)


def _clear_result() -> None:
    for key in ("conversion_result", "conversion_request", "conversion_error"):
        st.session_state[key] = None


def _swap_currencies() -> None:
    # Callbacks run before rendering, when widget keys can safely be updated.
    state = st.session_state
    state.source_currency_select, state.target_currency_select = (
        state.target_currency_select, state.source_currency_select
    )
    _clear_result()


def _number(value: Decimal) -> str:
    """Group digits without rounding away domain precision, including tiny results."""
    return format(value, ",f")


def _notice(element_id: str, message: str, kind: str) -> None:
    st.markdown(
        f'<div id="{element_id}" data-testid="{element_id}" class="notice {kind}" '
        f'role="alert">{escape(message)}</div>', unsafe_allow_html=True,
    )


def _render_result(result: ConversionResult, request: ConversionRequest) -> None:
    source, target = request.source_currency, request.target_currency
    same = source == target
    if same:
        status, color = "Same currency · no rate lookup", "neutral"
    elif result.is_offline:
        status, color = "Saved snapshot · offline", "amber"
    elif result.fallback_used:
        status, color = "Previous published date", "blue"
    else:
        status, color = "Official rate retrieved", "green"
    st.markdown(
        f'''<div id="conversion-result" data-testid="conversion-result" class="result-card">
        <span class="status {color}">{status}</span><p class="eyebrow result-label">YOU RECEIVE</p>
        <div id="result-amount" data-testid="result-amount" class="result-amount">
        {escape(_number(result.converted_amount))} <span>{target}</span></div>
        <p class="result-equation">{escape(_number(request.amount))} {source} → {target}</p>
        <div class="result-divider"></div>
        <div id="exchange-rate" data-testid="exchange-rate" class="rate-line">
        1 {source} = {escape(str(result.rate_used))} {target}</div>
        <p class="muted">{'Your amount stays unchanged.' if same else 'Reference rate per unit, rounded to 4 decimal places.'}</p></div>''',
        unsafe_allow_html=True,
    )
    if same:
        st.info("The currencies match. No BNM request was made; the date below is your selected date.")
    elif result.is_offline:
        _notice("offline-warning", result.message or "Using the last valid saved snapshot.", "warning")
    elif result.fallback_used and result.message:
        st.info(result.message)
    st.markdown(
        f'''<dl class="metadata">
        <div><dt>Requested date</dt><dd>{request.rate_date:%d.%m.%Y}</dd></div>
        <div id="effective-date" data-testid="effective-date"><dt>{'Selected date (no lookup)' if same else 'Effective rate date'}</dt>
        <dd>{result.effective_rate_date:%d.%m.%Y}</dd></div>
        <div id="source-name" data-testid="source-name"><dt>{'Configured source (not queried)' if same else 'Data source'}</dt>
        <dd>{escape(SOURCE_NAME)}<br><span class="muted">{escape(result.source_name)}</span></dd></div></dl>''', unsafe_allow_html=True,
    )
    with st.expander("How this result is calculated"):
        if same:
            st.write("Identical currencies return the original amount without rounding or looking up rates.")
        else:
            st.write("Amount × source rate in MDL ÷ target rate in MDL")
            st.write("BNM values are normalized per unit: Value ÷ Nominal. MDL has a base rate of 1.")
            st.write("The calculation uses Decimal and ROUND_HALF_UP: 2 decimal places, or 4 for positive results below 0.01. The displayed reference rate is rounded separately.")


def render_app() -> None:
    st.set_page_config(page_title="Currency Converter | BNM Rates", page_icon="💱", layout="wide", initial_sidebar_state="collapsed")
    _inject_custom_css()
    defaults = {
        "source_currency_select": "USD", "target_currency_select": "MDL",
        "amount_text_input": "100", "rate_date_picker": date.today(),
        "conversion_result": None, "conversion_request": None, "conversion_error": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    st.markdown('''<div class="brand-bar"><div class="brand"><span class="brand-icon">⇄</span>
        MOLDOVA <span class="brand-light">/ Currency tools</span></div>
        <span class="brand-note">OFFICIAL BNM DATA</span></div>
        <div class="hero"><p class="eyebrow">SIX CURRENCIES. ONE CLEAR RESULT.</p>
        <h1>Make every conversion <span>clear.</span></h1>
        <p class="hero-copy">Convert with official National Bank of Moldova exchange rates.
        See the date, source and rate behind your result.</p></div>''', unsafe_allow_html=True)
    form_col, result_col = st.columns([1.05, 1], gap="large")
    with form_col, st.container(border=True):
        st.markdown('<p class="eyebrow">01 / YOUR CONVERSION</p>', unsafe_allow_html=True)
        st.subheader("Choose your currencies")
        st.caption("Enter an amount, select a date, then convert.")
        raw = st.text_input("Amount", key="amount_text_input", placeholder="e.g. 100 or 25.50",
                            help="Positive decimal amount. A dot or comma can be used as the decimal separator.", on_change=_clear_result)
        parsed, validation_error = validate_amount(raw)
        if validation_error:
            _notice("validation-error", validation_error, "error")
        left, right = st.columns(2)
        with left:
            source = st.selectbox("From (Source Currency)", SUPPORTED_CURRENCIES, key="source_currency_select",
                                  format_func=lambda code: CURRENCY_NAMES[code], on_change=_clear_result)
        with right:
            target = st.selectbox("To (Target Currency)", SUPPORTED_CURRENCIES, key="target_currency_select",
                                  format_func=lambda code: CURRENCY_NAMES[code], on_change=_clear_result)
        st.button("⇄ Swap currencies", key="swap_currencies_btn", on_click=_swap_currencies, help="Exchange the source and target currencies.")
        rate_date = st.date_input("Exchange Rate Date (optional, defaults to today)", key="rate_date_picker",
                                  max_value=date.today(), on_change=_clear_result,
                                  help="If rates are unpublished, the service searches previous dates (up to 14 days).")
        st.caption("If a previous date or saved snapshot is used, its actual date is shown beside the result.")
        valid = parsed is not None and validation_error is None and rate_date is not None
        if st.button("Convert Currency", type="primary", key="convert_button", disabled=not valid, use_container_width=True) and valid:
            _clear_result()
            request = ConversionRequest(parsed, source, target, rate_date)
            with st.spinner("Fetching official exchange rates..."):
                try:
                    result = get_converter().convert(request)
                    st.session_state.conversion_result = result
                    st.session_state.conversion_request = request
                except (CurrencyUnavailableError, ExchangeRateUnavailableError) as exc:
                    st.session_state.conversion_error = str(exc)
                except Exception:
                    logging.getLogger(__name__).exception("Conversion failed unexpectedly")
                    st.session_state.conversion_error = "Conversion could not be completed. Check your connection or try another date."
        st.markdown('<p class="form-footnote">MDL · EUR · USD · RON · GBP · UAH</p>', unsafe_allow_html=True)
    with result_col, st.container(border=True):
        st.markdown('<p class="eyebrow">02 / THE RESULT</p>', unsafe_allow_html=True)
        st.subheader("Your conversion, explained")
        result, request = st.session_state.conversion_result, st.session_state.conversion_request
        if st.session_state.conversion_error:
            _notice("service-error", st.session_state.conversion_error, "error")
            st.caption("Adjust the details and try again. No result was produced.")
        elif result is not None and request is not None:
            _render_result(result, request)
        else:
            st.markdown('''<div class="empty-result"><div class="empty-symbol">⇄</div>
                <h3>Your result starts here</h3><p>Choose your currencies and select
                <strong>Convert Currency</strong>.</p><div class="empty-details">
                Converted amount<br>Effective rate date<br>Official source</div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-heading"><p class="eyebrow">BUILT AROUND TRANSPARENCY</p><h2>Know what goes into your conversion.</h2></div>', unsafe_allow_html=True)
    a, b, c = st.columns(3, gap="medium")
    for col, step, title, text in (
        (a, "01", "Official reference rates", "Rates come from the National Bank of Moldova XML feed. Foreign-currency values are normalized against the Moldovan leu."),
        (b, "02", "Dates you can verify", "Choose today or a past date. If no rate is published, the latest available prior date is used within a 14-day search window."),
        (c, "03", "Continuity when offline", "After a valid snapshot is saved, it remains available across restarts. Offline results are marked and show the real saved date."),
    ):
        with col:
            st.markdown(f'<div class="info-card"><span class="step">{step}</span><h3>{title}</h3><p>{text}</p></div>', unsafe_allow_html=True)
    with st.expander("About the supported currencies and rates"):
        st.write(" · ".join(CURRENCY_NAMES.values()))
        st.write("Official reference rates may differ from the rate offered by a bank or exchange office. This educational tool does not include transaction fees.")
        st.markdown("[Visit the National Bank of Moldova](https://www.bnm.md/en/official_exchange_rates)")
    st.markdown('<div class="footer"><span>Currency Converter <strong>/ SDD laboratory</strong></span><span>National Bank of Moldova · Reference rates</span></div>', unsafe_allow_html=True)
