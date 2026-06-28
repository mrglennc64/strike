# Domain Registration & Setup Guide for edge-ai.io

**Target Domain:** `edge-ai.io`  
**Current Date:** 2026-06-28

---

## Quick Setup (5 minutes)

### Option 1: Using Namecheap (Recommended)

1. **Go to** https://www.namecheap.com
2. **Search** for `edge-ai.io` in domain search
3. **Add to cart** and proceed to checkout
4. **Cost:** ~$8.98/year
5. **Complete purchase** with PayPal or credit card
6. **Skip Namecheap nameservers** - we'll use Cloudflare or Vercel DNS

### Option 2: Using Route53 (AWS)

```bash
# If you have AWS account
aws route53 register-domain-charge \
  --domain-name edge-ai.io \
  --duration-in-years 1
```

### Option 3: Using Cloudflare Registrar

1. **Go to** https://www.cloudflare.com/products/registrar/
2. **Login** to Cloudflare account
3. **Search** for `edge-ai.io`
4. **Register** directly
5. **Cost:** $8.85/year (no markup)

---

## DNS Configuration

### If Using Vercel + Railway

**Add these DNS records to your registrar:**

```
SUBDOMAIN          TYPE    VALUE                           TTL
─────────────────────────────────────────────────────────────
@                  CNAME   cname.vercel-dns.com            3600
www                CNAME   cname.vercel-dns.com            3600
api                CNAME   edge-ai-api.railway.app         3600
docs               CNAME   cname.vercel-dns.com            3600
status             CNAME   status-page.io                  3600
```

### If Using Cloudflare

After registering:

1. **Go to** https://dash.cloudflare.com
2. **Add site** → `edge-ai.io`
3. **Copy nameservers** provided by Cloudflare
4. **Update at Namecheap:**
   - Dashboard → Domain List
   - edge-ai.io → Manage
   - Nameservers → Custom DNS
   - Paste Cloudflare nameservers

5. **Then add DNS records in Cloudflare:**

```
Name               Type    Content                         TTL
─────────────────────────────────────────────────────────────
edge-ai.io         A       Vercel IP (auto-detected)       Auto
www                CNAME   cname.vercel-dns.com            Auto
api                CNAME   edge-ai-api.railway.app         Auto
docs               CNAME   cname.vercel-dns.com            Auto
_acme-challenge    TXT     (Let's Encrypt auto-filled)     Auto
```

---

## Step-by-Step: Namecheap Setup

### 1. Purchase Domain

```
Website:  https://www.namecheap.com
Search:   edge-ai.io
Price:    $8.98/year (+ $1.58 ICANN fee)
Total:    ~$10.56/year
```

### 2. Access Domain Settings

- **Login** to Namecheap account
- **Go to:** Dashboard → Domain List
- **Find:** edge-ai.io
- **Click:** Manage

### 3. Change Nameservers to Vercel

If using Vercel for DNS:

1. **Click:** Nameservers
2. **Select:** Custom DNS
3. **Add Vercel nameservers:**
   ```
   dns.vercel.com
   dns1.vercel.com
   dns2.vercel.com
   dns3.vercel.com
   ```
4. **Save**

**Wait:** 24-48 hours for propagation

### 4. Configure Subdomains in Vercel

1. **Go to:** https://vercel.com/dashboard
2. **Select project:** Edge AI
3. **Settings** → Domains
4. **Add Domain:** edge-ai.io
5. **Verify** with DNS record
6. **Add Subdomains:**
   - www.edge-ai.io
   - api.edge-ai.io (optional, if not using Railway custom domain)

### 5. Verify Domain Propagation

```bash
# Check nameserver propagation
nslookup edge-ai.io

# Should return Vercel's nameservers

# Check DNS records
dig edge-ai.io
dig www.edge-ai.io
dig api.edge-ai.io

# Verify SSL (auto-provisioned by Vercel)
curl -I https://edge-ai.io
curl -I https://www.edge-ai.io
curl -I https://api.edge-ai.io
```

---

## Step-by-Step: Cloudflare Setup

### 1. Create Cloudflare Account

- Go to https://dash.cloudflare.com/sign-up
- Register with email
- Create account

### 2. Add Site to Cloudflare

1. **Click:** + Add Site
2. **Enter:** edge-ai.io
3. **Select Plan:** Free ($0)
4. **Continue**

### 3. Copy Cloudflare Nameservers

Cloudflare will provide:
```
NS Server 1: abc1.ns.cloudflare.com
NS Server 2: def2.ns.cloudflare.com
```

### 4. Update Nameservers at Namecheap

1. **Login** to Namecheap
2. **Go to:** Dashboard → Domain List
3. **Find:** edge-ai.io
4. **Click:** Manage
5. **Go to:** Nameservers
6. **Select:** Custom DNS
7. **Paste Cloudflare nameservers:**
   ```
   abc1.ns.cloudflare.com
   def2.ns.cloudflare.com
   ```
8. **Save Changes**

### 5. Add DNS Records in Cloudflare

In Cloudflare Dashboard:

1. **Click:** DNS
2. **Add records:**

```
Type    Name            Content                         TTL     Proxy
──────────────────────────────────────────────────────────────────────
CNAME   www             cname.vercel-dns.com            Auto    Proxied
CNAME   api             edge-ai-api.railway.app         Auto    DNS only
A       edge-ai.io      (Vercel IP from Vercel)         Auto    Proxied
```

### 6. Verify in Vercel

1. **Go to:** https://vercel.com/dashboard
2. **Select:** Edge AI project
3. **Settings** → Domains
4. **Add:** edge-ai.io
5. **Verify** ownership (Cloudflare will handle)

### 7. Enable SSL/TLS

In Cloudflare:

1. **Go to:** SSL/TLS
2. **Select:** Full (recommended)
3. **Edge Certificates:** Auto (enabled)

In Vercel:

- SSL auto-provisioned
- Check:** Settings → SSL/TLS

---

## Email Setup (Optional)

If you want email forwarding for `@edge-ai.io`:

### Using Namecheap Email Forwarding

1. **Dashboard** → edge-ai.io → Manage
2. **Email Forwarding**
3. **Add forwarding rule:**
   ```
   From: support@edge-ai.io
   To: your-email@gmail.com
   ```

### Using Cloudflare Email Routing

1. **Cloudflare Dashboard**
2. **Email Routing**
3. **Add custom domain:** edge-ai.io
4. **Create routing rules:**
   ```
   support@edge-ai.io → your-email@gmail.com
   hello@edge-ai.io → your-email@gmail.com
   ```

---

## Subdomain Configuration

### Complete DNS Setup

```
Primary Domain
  edge-ai.io                CNAME → Vercel
  www.edge-ai.io            CNAME → Vercel

Application Subdomains
  api.edge-ai.io            CNAME → Railway (backend)
  docs.edge-ai.io           CNAME → Vercel (same as main)
  
Monitoring Subdomains
  status.edge-ai.io         CNAME → Statuspage.io
  analytics.edge-ai.io      CNAME → Analytics provider
  
Email (Optional)
  mail.edge-ai.io           A/MX → Email provider
```

### Configure in Railway

```bash
# Connect custom domain to Railway backend
railway domain add api.edge-ai.io

# Verify
railway domain list

# Get verification code if needed
railway domain verify api.edge-ai.io
```

### Configure in Vercel

```bash
# Add domains to project
vercel domains add edge-ai.io
vercel domains add www.edge-ai.io
vercel domains add docs.edge-ai.io

# Verify domains
vercel domains verify edge-ai.io
```

---

## Verification Checklist

- [ ] Domain purchased (edge-ai.io)
- [ ] Nameservers updated (24-48 hours)
- [ ] DNS records propagated
- [ ] Vercel domain verified
- [ ] Railway custom domain configured
- [ ] SSL certificate active
- [ ] Frontend accessible via https://edge-ai.io
- [ ] Backend accessible via https://api.edge-ai.io
- [ ] API health check: `curl https://api.edge-ai.io/health`
- [ ] All 5 verticals responding

---

## Testing Domain Access

```bash
# Test all endpoints
echo "Testing edge-ai.io domains..."

# Main site
curl -I https://edge-ai.io
curl -I https://www.edge-ai.io

# API backend
curl -I https://api.edge-ai.io/health
curl https://api.edge-ai.io/health | jq

# API verticals
curl https://api.edge-ai.io/api/verticals | jq
curl https://api.edge-ai.io/api/verticals/mlb | jq

# DNS propagation checker
dig +short edge-ai.io
dig +short api.edge-ai.io
dig +short www.edge-ai.io

# Whois lookup
whois edge-ai.io
```

---

## Troubleshooting

### Domain Not Resolving

```bash
# Clear DNS cache
sudo systemctl restart systemd-resolved  # Linux
sudo dscacheutil -flushcache            # macOS
ipconfig /flushdns                       # Windows

# Wait 24-48 hours for propagation
# Check status at: https://www.whatsmydns.net/

# Verify nameservers
nslookup edge-ai.io
# Should show: ns1.vercel-dns.com, etc.
```

### SSL Certificate Not Working

```bash
# Force Vercel to regenerate certificate
vercel certs ls
vercel certs create edge-ai.io
vercel certs verify edge-ai.io

# Check certificate validity
openssl s_client -connect api.edge-ai.io:443
```

### Subdomain Not Working

```bash
# Verify CNAME record
dig api.edge-ai.io
# Should return: CNAME to edge-ai-api.railway.app

# Check Railway configuration
railway domain verify api.edge-ai.io

# Test from different DNS resolvers
nslookup api.edge-ai.io 8.8.8.8       # Google DNS
nslookup api.edge-ai.io 1.1.1.1       # Cloudflare DNS
```

---

## Renewal & Maintenance

### Auto-Renewal

- **Namecheap:** Auto-renewal enabled (no action needed)
- **Vercel:** Manages SSL certs automatically
- **Railway:** Manages SSL certs automatically

### Annual Tasks

- [ ] Verify domain registration status
- [ ] Check SSL certificate expiration (Vercel/Railway auto-renew)
- [ ] Review DNS records
- [ ] Test domain accessibility

### Cost Breakdown (Annual)

```
Domain Registration (Namecheap)  $10.56
SSL Certificate (Vercel)          FREE
CDN & Hosting (Vercel)            FREE (up to 100GB)
Backend Hosting (Railway)         ~$7-20/month
Database (PostgreSQL)             ~$5-15/month
Cache (Redis)                     ~$2-5/month
───────────────────────────────────────
Approximate Annual Cost:          $150-200
```

---

## Resources

- **Namecheap Dashboard:** https://www.namecheap.com/myaccount
- **Vercel Domains:** https://vercel.com/dashboard/domains
- **Railway Domains:** https://railway.app/dashboard
- **DNS Checker:** https://www.whatsmydns.net
- **SSL Checker:** https://www.sslshopper.com/ssl-checker.html

---

**Domain Status:** 🔵 Ready for Registration  
**Last Updated:** 2026-06-28  
**Support:** support@edge-ai.io
