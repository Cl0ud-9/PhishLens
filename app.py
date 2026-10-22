"""PhishLens in the browser: paste a link, see whether its domain looks like a phishing domain, and why."""
import altair as alt
import pandas as pd
import streamlit as st

from phishlens import PhishLens, check

LEVEL_STYLE = {"high": st.error, "ip": st.error, "uncertain": st.warning, "low": st.success, "official": st.success}
EXAMPLES = {"Brand + login words": "https://paypal-secure-login-verify.com/signin",
            "Fake Google address": "https://accounts.google.com.verify-session.top/login",
            "A genuine site": "https://www.viit.ac.in",
            "Look-alike letters": "https://pаypal.com"}
SHORT = {"length": "name length", "digits": "digits", "digit_ratio": "share of digits", "hyphens": "hyphens",
         "vowel_ratio": "share of vowels", "consonant_run": "consonant run", "entropy": "character variety",
         "unique_ratio": "distinct characters", "brand_exact": "is a brand", "brand_inside": "borrows a brand",
         "action_words": "'login'-type words", "punycode": "punycode", "suffix_levels": "suffix parts",
         "suffix": "ending", "name_pattern": "letter patterns"}
RAISES, LOWERS = "#c0392b", "#2e7d32"


@st.cache_resource
def load_model():
    return PhishLens.load()


def why_chart(reasons):
    data = pd.DataFrame({"feature": [SHORT[r.feature] for r in reasons], "effect": [r.contribution for r in reasons],
                         "reason": [r.text for r in reasons]})
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("effect:Q", title="effect on the risk (log-odds)"),
        y=alt.Y("feature:N", sort=None, title=None),
        color=alt.condition(alt.datum.effect > 0, alt.value(RAISES), alt.value(LOWERS)),
        tooltip=["reason", alt.Tooltip("effect:Q", format="+.2f")],
    ).properties(height=34 * len(data))


st.set_page_config(page_title="PhishLens", page_icon="🔎")
st.title("🔎 PhishLens")
st.caption("Does this link's domain look like a phishing domain, and why? The link is only read, never opened.")

if "url" not in st.session_state:
    st.session_state.url = ""
for col, (label, example) in zip(st.columns(len(EXAMPLES)), EXAMPLES.items()):
    if col.button(label, help=example, use_container_width=True):
        st.session_state.url = example
url = st.text_input("Link to check", key="url", placeholder="https://example.com/login")

if url:
    try:
        verdict = check(url, load_model())
    except ValueError as error:
        st.error(f"That does not look like a link: {error}")
        st.stop()
    score = f" — {verdict.score:.0%} phishing risk" if verdict.score is not None else ""
    LEVEL_STYLE[verdict.level](f"**{verdict.summary}**{score}")
    st.markdown(f"Domain judged: `{verdict.domain}`")
    for note in verdict.notes:
        st.info(note)
    if verdict.reasons:
        st.subheader("Why")
        st.caption("SHAP values from the model: how much each feature moved this link's risk, largest first. "
                   "Red raises the risk, green lowers it.")
        st.altair_chart(why_chart(verdict.reasons), use_container_width=True)
        for r in verdict.reasons:
            st.markdown(f"{'🔺' if r.contribution > 0 else '🔻'} {r.text} ({r.contribution:+.2f})")

st.divider()
st.caption("PhishLens judges the domain name only. A domain that looks fine can still host a phishing page, so treat "
           "a low score as 'no red flags in the name', not as proof that a site is safe.")
