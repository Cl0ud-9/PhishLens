"""Official domains of brands that phishers imitate.

The model judges how a name looks, and a brand's own name looks just like the fakes that borrow it. These domains are
recognised before the model is asked. The list is checked against the registered domain only, so
google.com.example.xyz or accounts-google.com are not on it. The reported accuracy does not use this list.
"""

OFFICIAL = {
    "adobe.com": "Adobe", "amazon.com": "Amazon", "amazon.in": "Amazon", "amazon.co.uk": "Amazon",
    "apple.com": "Apple", "icloud.com": "Apple", "axisbank.com": "Axis Bank", "binance.com": "Binance",
    "chase.com": "Chase", "coinbase.com": "Coinbase", "dhl.com": "DHL", "docusign.com": "DocuSign",
    "dropbox.com": "Dropbox", "facebook.com": "Facebook", "fedex.com": "FedEx", "github.com": "GitHub",
    "gmail.com": "Google", "google.com": "Google", "google.co.in": "Google", "google.co.uk": "Google",
    "hdfcbank.com": "HDFC Bank", "hsbc.com": "HSBC", "icicibank.com": "ICICI Bank", "instagram.com": "Instagram",
    "irctc.co.in": "IRCTC", "linkedin.com": "LinkedIn", "live.com": "Microsoft", "metamask.io": "MetaMask",
    "microsoft.com": "Microsoft", "netflix.com": "Netflix", "office.com": "Microsoft", "onlinesbi.sbi": "SBI",
    "outlook.com": "Microsoft", "paypal.com": "PayPal", "paytm.com": "Paytm", "phonepe.com": "PhonePe",
    "sbi.co.in": "SBI", "twitter.com": "X (Twitter)", "usps.com": "USPS", "wellsfargo.com": "Wells Fargo",
    "whatsapp.com": "WhatsApp", "wikipedia.org": "Wikipedia", "x.com": "X (Twitter)", "yahoo.com": "Yahoo",
    "youtube.com": "YouTube",
}
