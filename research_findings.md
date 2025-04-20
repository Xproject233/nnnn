# Research Findings: Security Guard Job Posting Websites

## Job Boards
1. **LinkedIn** - https://www.linkedin.com/jobs/security-guard-jobs
   - Contains company names, locations, and job details
   - Requires authentication for full access
   - Has a large database of security guard positions (140,000+ listings)

2. **Indeed** - https://www.indeed.com/q-construction-security-guard-jobs.html
   - Contains detailed job listings with company information
   - Has specific construction security guard listings
   - May have anti-scraping measures (Cloudflare protection)

3. **Security Jobs Network** - https://securityjobs.net/
   - Specialized job board for security professionals
   - Employers post jobs directly on the platform
   - Contains "curated job leads for security professionals"

4. **Security Guards Only** - https://www.securityguardsonly.com/
   - Specialized job board for security guards in North America
   - Contains company information and job details
   - Connects employers with job seekers in the security industry

5. **GardaWorld** - https://securityjobsus.garda.com/
   - Security company with job listings
   - Contains direct employer contact information

6. **Allied Universal** - https://jobs.aus.com/security-professional-positions
   - Major security company with job listings
   - Contains direct employer contact information

7. **Securitas** - https://www.securitasinc.com/careers/apply/
   - Major security company with job listings
   - Contains direct employer contact information

8. **Security Guards United** - https://security-guard-jobs.jobboardly.com/
   - Specialized job board for security guards
   - Contains company information and job details

## Government Job Sites
1. **USAJOBS** - https://www.usajobs.gov/Search/?soc=Security%20Guards
   - Federal government job listings for security guards
   - Contains detailed department and agency information
   - Has structured data with salary, location, and job requirements

## Government Contract & RFP Sites
1. **InstantMarkets** - https://www.instantmarkets.com/q/event_security_guard
   - Contains RFPs and contract opportunities for security services
   - Includes agency names, contact details, and bid deadlines
   - Has structured data with detailed RFP information

2. **BidNetDirect** - https://www.bidnetdirect.com/public/solicitations/open?keywords=Security+Services
   - Contains security service contract opportunities
   - Includes agency information, locations, and closing dates
   - Has structured data with detailed bid information

3. **FindRFP** - http://findrfp.com/security-safety-bids/security-guard.aspx
   - Specialized in security guard RFPs and government contracts
   - Contains contact information for contracting agencies

## Other Potential Sources
1. **Event venues and convention centers websites** - May post security service needs
2. **Construction company websites** - Often have security needs for construction sites
3. **Local government procurement websites** - Post security service contracts

## Data Availability Analysis
Most of these websites contain the following information that can be extracted:
- Company/Agency Names: Available on all sites
- Email Addresses: Available in RFP documents and some job postings
- Phone Numbers: Available in RFP documents and some job postings
- Job/Contract Details: Available on all sites

## Scraping Feasibility
- Job boards like LinkedIn and Indeed have anti-scraping measures
- Government contract sites like InstantMarkets and BidNetDirect appear more accessible
- Specialized security job boards may have fewer restrictions

## Recommended Primary Targets for Scraping
1. InstantMarkets (RFPs for security services)
2. BidNetDirect (Security service contracts)
3. USAJOBS (Government security positions)
4. Security Jobs Network (Specialized security job board)
5. Security Guards Only (Specialized security job board)
