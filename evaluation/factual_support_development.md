# Factual-support checker development set

> Development data only. This is not a holdout or a general accuracy benchmark. All current grades are proposals until a human reviewer approves them.

## Readiness

- Fact cases: 30 across 2 real companies.
- Proposed grades: 16 supported, 8 partial, 6 unsupported.
- Discovery-question cases: 4 (excluded from the fact-case count).
- Human-approved fact labels: 0.
- Ready for reference evaluation: **no**.
- Exact gap: the proposed case-count/class-balance targets are met, but only two real companies are represented and no taxonomy labels have human approval.

## Labeling rubric

- **Supported:** The cited evidence supports the entire claim.
- **Partial:** The cited evidence supports a substantive part of the claim, but another clause or qualifier is missing.
- **Unsupported:** The cited evidence does not establish the claim's central assertion. Unsupported does not necessarily mean contradicted or false.

## Evidence inventory

- `keri-home-20261005` — Keri Shull Team, https://kerishull.com/, fetched 2026-10-05T16:45:04.517401+00:00; 480,787 bytes; complete reader snapshot: true.
- `jills-home-20260927` — The Jills Zeder Group, https://jillszeder.com/, fetched 2026-09-27T14:10:48.266541+00:00; 160,191 bytes; complete reader snapshot: true.
- `jills-home-live-20260927` — The Jills Zeder Group, https://jillszeder.com/, fetched 2026-09-27T12:28:02.707619+00:00; 159,590 bytes; complete reader snapshot: true.
- `jills-about-20260927` — The Jills Zeder Group, https://jillszeder.com/about-us/, fetched 2026-09-27T12:28:14.641256+00:00; 105,241 bytes; complete reader snapshot: true.
- `jills-list-with-us-20260927` — The Jills Zeder Group, https://jillszeder.com/list-with-us/, fetched 2026-09-27T12:28:20.934265+00:00; 113,187 bytes; complete reader snapshot: true.
- `jills-contact-us-20260927` — The Jills Zeder Group, https://jillszeder.com/contact-us/, fetched 2026-09-27T12:28:25.154017+00:00; 103,867 bytes; complete reader snapshot: true.

### Excluded evidence

- Bartic Group (barticgroup.com): Truncated oversized-response prefix, not a completed reader snapshot; excluded from claim/evidence cases.
- Matt O'Neill Real Estate (www.mattoneillrealestate.com): Provider failed before any page fetch; no evidence snapshot exists.
- Harbor Example Realty (team.example): Synthetic fixture company; excluded from real-company development counts.

## Review history

- **Keri Shull Team:** Six agent facts and two questions. The user explicitly identified the off-market strategy strengthening, generic guarantee citation, split consent citation, and unsupported sales assumptions. The supported/partial/unsupported taxonomy grades in this dataset remain unapproved proposals.
- **The Jills Zeder Group:** Multiple Codex claim-by-claim reviews exist for v1, source-ID, and atomic runs. They are AI-proposed review history, not human-approved reference labels.

## Bounded third-company capture plan

1. Before selection, designate one real estate company outside Keri Shull and Jills Zeder as development-only and exclude it from the future acceptance sample; choose a public homepage readable under the unchanged 250,000-byte cap.
2. Use WebsiteReader directly without a generator or verifier. Capture the homepage and at most two relevant same-host pages selected from discovered links; retain exact normalized text, source and final URLs, timestamps, normalized text hashes, and every reader outcome, including redirects, observed bytes, declared size, completeness, or failure.
3. Create eight nonduplicate fact cases spanning identity, service/form observations, qualifiers, reporting periods, and workflow-assumption challenges, targeting four clearly supported and four partial/unsupported proposals without manufacturing unsupported wording solely to satisfy balance.
4. Have a human reviewer approve or correct the full reference set without showing labels to the verifier; only human-approved fact labels count toward the issue gate.

### Suggested supported controls

- Company identity or brokerage affiliation stated on the captured page.
- A named service or market area stated without adding a qualifier.
- A numeric result with its metric and reporting period retained when present.
- A directly observable form field or contact channel described only as visible on the page.

### Suggested challenging cases

- A claim whose cited span mentions the topic but omits a named service, qualifier, or reporting period.
- A bundled claim for which one substantive clause lacks support in the retained references.
- A form-to-workflow claim that infers routing, response time, automation, or intent from visible fields.
- A historical outcome reframed as a current service, guarantee, or operating practice.

## Fact cases

### KERI-F001 — Keri Shull Team

- Candidate: The website — identifies the organization as: Keri Shull Team
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited title names the Keri Shull Team.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — new control derived from saved evidence
- Evidence `keri-home-20261005/S1/E1` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [0, 599):

  > Virginia, Maryland, & DC Real Estate Agents | Keri Shull Team Home Search Home Valuation Cities Contact Us menu About About Us Careers Giving Back Properties Featured Properties Past Transactions Arlington Properties Home Search Arlington Alexandria Washington DC Falls Church Vienna McLean Search All Homes Cities Discover Arlington Home Valuation Client Success Stories Guarantees Buyer Guarantee Seller Guarantee Move Up Guarantees Relocation Guarantees Mortgage Calculator Financing Options Press & Media Condos Blog All Blogs Lifestyle Blogs Real Estate Blogs Videos Contact Us My Search Portal

### KERI-F002 — Keri Shull Team

- Candidate: The Keri Shull Team website — reports serving: Virginia, Maryland, and DC
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt explicitly names all three jurisdictions.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — new control derived from saved evidence
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F003 — Keri Shull Team

- Candidate: The Keri Shull Team website — reports a client database of: 159,000+ clients who receive newsletters and marketing campaigns
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The number and described newsletter/marketing use appear together in the cited excerpt.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — new control derived from saved evidence
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F004 — Keri Shull Team

- Candidate: The Keri Shull Team website — reports sales volume of: $5B+
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt explicitly displays “$5B+ in sales volume.”
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — new control derived from saved evidence
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F005 — Keri Shull Team

- Candidate: The Keri Shull Team website — reports social-media followers totaling: 70K+
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt explicitly displays “70K+ Followers.”
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — new control derived from saved evidence
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F006 — Keri Shull Team

- Candidate: The Keri Shull Team website — reports that the share of deals sold off-market exceeds: 22%
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt explicitly reports that over 22% of deals were sold off-market.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — new control derived from saved evidence
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F007 — Keri Shull Team

- Candidate: The Keri Shull Team website — describes the team as: the Top Producing Real Estate Team in the DC Metro area
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The description appears verbatim and is attributed to the website rather than independently asserted.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — new control derived from saved evidence
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F008 — Keri Shull Team

- Candidate: Keri Shull Team — offers seller services including: an off-market sales strategy
- Proposed grade: **unsupported**
- Unsupported clause: offers seller services including an off-market sales strategy
- Explanation: The excerpt reports a past share of off-market deals, but that observation does not establish the claim's central assertion that an off-market seller strategy is currently offered. Unsupported here does not mean the strategy is false or contradicted.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — run 4686ade6e2f34706ae3161249d46a97e C4
- Label history: **partial** (`superseded_unreviewed_proposal`) — The initial proposal treated the historical off-market result as substantive support. Under the clarified rubric, it does not establish the central offered-strategy assertion.
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F009 — Keri Shull Team

- Candidate: Keri Shull Team — offers client guarantee programs including: buyer, seller, move-up, and relocation guarantees
- Proposed grade: **partial**
- Unsupported clause: buyer, seller, move-up, and relocation guarantees
- Explanation: The excerpt supports that several guarantee programs exist but does not name the four programs.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — run 4686ade6e2f34706ae3161249d46a97e C5
- Evidence `keri-home-20261005/S1/E3` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [1189, 1599):

  > The team has helped thousands of families buy or sell their home in VA, DC, & MD. Keri offers her clients several GUARANTEE programs that eliminate the typical risks associated with buying or selling properties. Get in touch today for amazing results! Play Video Neighborhoods Washington Arlington Alexandria Falls Church McLean Vienna Fairfax Leesburg Chevy Chase Bethesda View All Client Success Stories 1 B.

### KERI-F010 — Keri Shull Team

- Candidate: The Keri Shull Team website — includes a contact form with consent for contact via: call, email, and text message
- Proposed grade: **partial**
- Unsupported clause: call, email, and text message
- Explanation: This continuation mentions text and opt-out terms but omits the beginning of the consent sentence establishing agreement to call and email contact.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — run 4686ade6e2f34706ae3161249d46a97e C6
- Evidence `keri-home-20261005/S1/E12` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [6244, 6666):

  > text for real estate services. To opt out, you can reply 'stop' at any time or reply 'help' for assistance. You can also click the unsubscribe link in the emails. Message and data rates may apply. Message frequency may vary. Privacy Policy . Submit Sending... Sent! T: 703-609-5183 E: [email protected] × Thanks, please provide more information to help serve you Email Trigger Source Phone Number Interest Interested in...

### KERI-F011 — Keri Shull Team

- Candidate: The Keri Shull Team website form — automatically routes: every inquiry to an available agent
- Proposed grade: **unsupported**
- Unsupported clause: automatically routes every inquiry to an available agent
- Explanation: The form and consent text do not describe automated routing, delivery, recipients, or operational behavior.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `deliberately_constructed_challenge` — form-to-workflow assumption built from saved Keri form evidence
- Evidence `keri-home-20261005/S1/E11` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [5646, 6243):

  > Brentwood Homes Temple Hills Homes Vienna Homes Springfield Homes Suitland Homes Kensington Homes Bladensburg Homes Fort Washington Homes Follow Us Address 3060 Williams Dr Suite 300 Fairfax, VA 22031 Contact Email: [email protected] Phone: 703-609-5183 Follow About Us Featured Properties Testimonials Contact Guild Mortgage Privacy Policy Real Estate Website Design by Luxury Presence © Copyright 2026 | Privacy Policy link Ask Us Anything! Middle Name Name Email Phone Message Opt In/Disclaimer Consent: I agree to be contacted by Keri Shull Team and Guild Mortgage Company via call, email, and

- Evidence `keri-home-20261005/S1/E12` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [6244, 6666):

  > text for real estate services. To opt out, you can reply 'stop' at any time or reply 'help' for assistance. You can also click the unsubscribe link in the emails. Message and data rates may apply. Message frequency may vary. Privacy Policy . Submit Sending... Sent! T: 703-609-5183 E: [email protected] × Thanks, please provide more information to help serve you Email Trigger Source Phone Number Interest Interested in...

### KERI-F012 — Keri Shull Team

- Candidate: Keri Shull Team — responds quickly to: all incoming leads
- Proposed grade: **unsupported**
- Unsupported clause: responds quickly to all incoming leads
- Explanation: The evidence is one customer testimonial about an individual agent during a transaction, not a team-wide lead-response policy or measured performance.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `deliberately_constructed_challenge` — wrong-subject and wrong-excerpt challenge from saved testimonial
- Evidence `keri-home-20261005/S1/E4` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [1600, 2195):

  > WILLIS "It took a little while because the market is rolling over fast here in NOVA but Kyle with the Shull team worked really hard and was very smart with the market here and all the paperwork that comes with buying a place. He pretty much worked 7 days a week since we called, texted, and emailed him during the process after work and on Saturday and Sunday. Thanks a lot Kyle! We were searching for a house or condo and there were a lot but they would go very fast. I would recommend the team!" 2 MATT B. “My wife and I recently closed on a beautiful single family home in Northern Arlington.

### KERI-F013 — Keri Shull Team

- Candidate: Keri Shull Team — has sold nearly $5 billion since 2021 and is: the top-producing DC Metro team
- Proposed grade: **partial**
- Unsupported clause: since 2021
- Explanation: The excerpt supports the sales figure and website ranking claim but contains no “since 2021” reporting period.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `deliberately_constructed_challenge` — missing-period bundled-assertion challenge
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F014 — Keri Shull Team

- Candidate: Keri Shull Team — has an active client database of: 159,000+ people
- Proposed grade: **partial**
- Unsupported clause: active
- Explanation: The excerpt reports a client database used for newsletters and campaigns but does not establish that every record is active.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `deliberately_constructed_challenge` — unsupported-qualifier challenge
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-F015 — Keri Shull Team

- Candidate: Keri Shull Team guarantee programs — eliminate: all transaction risks for buyers and sellers
- Proposed grade: **partial**
- Unsupported clause: all transaction risks
- Explanation: The marketing copy says the programs eliminate “typical risks”; it does not support the absolute qualifier “all.”
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `deliberately_constructed_challenge` — unsupported-absolute-qualifier challenge
- Evidence `keri-home-20261005/S1/E3` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [1189, 1599):

  > The team has helped thousands of families buy or sell their home in VA, DC, & MD. Keri offers her clients several GUARANTEE programs that eliminate the typical risks associated with buying or selling properties. Get in touch today for amazing results! Play Video Neighborhoods Washington Arlington Alexandria Falls Church McLean Vienna Fairfax Leesburg Chevy Chase Bethesda View All Client Success Stories 1 B.

### JILLS-F001 — The Jills Zeder Group

- Candidate: The Jills Zeder Group — is affiliated with: Coldwell Banker Realty
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt explicitly states the affiliation.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — archived atomic run C2; AI-proposed review marked supported
- Evidence `jills-home-20260927/S1/E7` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [3256, 3837):

  > The Jills® and The Zeder Team combining over four decades of experience, unparalleled expertise, and superior business savvy have come together to become The Jills Zeder Group, affiliated with Coldwell Banker Realty. The Jills Zeder Group is a powerhouse team of real estate experts specializing in the most magnificent properties in South Florida. And with their increased footprint, global reach, and worldwide marketing platform, The Jills Zeder Group has closed over $13 Billion worth of sales. Their combined track record speaks for itself: you are in extremely capable hands.

### JILLS-F002 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website — reports closed sales exceeding: $13 billion
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt explicitly reports closed sales over $13 billion.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — archived atomic run C4; AI-proposed review marked supported
- Evidence `jills-home-20260927/S1/E7` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [3256, 3837):

  > The Jills® and The Zeder Team combining over four decades of experience, unparalleled expertise, and superior business savvy have come together to become The Jills Zeder Group, affiliated with Coldwell Banker Realty. The Jills Zeder Group is a powerhouse team of real estate experts specializing in the most magnificent properties in South Florida. And with their increased footprint, global reach, and worldwide marketing platform, The Jills Zeder Group has closed over $13 Billion worth of sales. Their combined track record speaks for itself: you are in extremely capable hands.

### JILLS-F003 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website — reports more than $13 billion in sales: since 2021
- Proposed grade: **partial**
- Unsupported clause: since 2021
- Explanation: The amount appears, but the cited excerpt omits the “since 2021” period found in an uncited neighboring span.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — archived atomic/source-ID reviews: reporting-period omission
- Evidence `jills-home-20260927/S1/E7` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [3256, 3837):

  > The Jills® and The Zeder Team combining over four decades of experience, unparalleled expertise, and superior business savvy have come together to become The Jills Zeder Group, affiliated with Coldwell Banker Realty. The Jills Zeder Group is a powerhouse team of real estate experts specializing in the most magnificent properties in South Florida. And with their increased footprint, global reach, and worldwide marketing platform, The Jills Zeder Group has closed over $13 Billion worth of sales. Their combined track record speaks for itself: you are in extremely capable hands.

### JILLS-F004 — The Jills Zeder Group

- Candidate: The Jills Zeder Group — is ranked: the #1 real estate team in the U.S.A. in 2026
- Proposed grade: **unsupported**
- Unsupported clause: the #1 real estate team in the U.S.A. in 2026
- Explanation: The cited excerpt contains neither the #1 ranking nor the 2026 qualifier.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — archived atomic run C1 and AI-proposed review
- Evidence `jills-home-20260927/S1/E4` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [1755, 2070):

  > You can reply "STOP" at any time to opt-out. Message and data rates may apply. Message frequency may vary. Text "HELP" for assistance. For more information, please visit our Privacy Policy and SMS Terms & Conditions . Please prove you are human by selecting the key . Sign Up Now Play Real Estate Team in the U.S.A.

### JILLS-F005 — The Jills Zeder Group

- Candidate: The Jills Zeder Group — serves: Miami Beach and Coral Gables, Florida
- Proposed grade: **partial**
- Unsupported clause: Florida
- Explanation: Miami Beach and Coral Gables are stated, but the selected span does not attach the Florida qualifier to both markets.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — archived atomic run C3 and AI-proposed review
- Evidence `jills-home-20260927/S1/E5` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [2071, 2666):

  > Servicing Miami Beach and Coral Gables FOR THE 6TH YEAR IN A ROW AS RANKED IN 2026 REALTRENDS VERIFIED AS PUBLISHED IN THE WALL STREET JOURNAL Let's Get Started Learn More I am a buyer I am a seller Schedule Consultation Featured Listings View Details Key Biscayne 485 Matheson Drive $237,000,000 5 Beds 9 Baths 11,528 SqFt View Details Golden Beach 355 Ocean Boulevard $89,000,000 13 Beds 21 Baths 23,695 SqFt View Details Golden Beach 105 + 115 Ocean Boulevard $67,500,000 10 Beds 18 Baths 13,323 SqFt View Details Golden Beach 105 + 115 Ocean Boulevard $67,500,000 View Details Miami Beach 36

### JILLS-F006 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website — lists an office in: Miami Beach
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt labels a Miami Beach office and gives its address.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — narrow control from archived source-ID C3 evidence
- Evidence `jills-home-20260927/S1/E2` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [595, 1194):

  > Luxury Rentals Buyers Buy With Us Neighborhood Guides Relocation Sellers List With Us Our Numbers Marketing Masters Global Connections Industry Experts Distinctive Sales About Us The Jills Zeder Group Client Reviews In The Media Blog Press Videos Contact Us MIAMI BEACH OFFICE 305.341.7447 1682 Jefferson Avenue Miami Beach, FL 33139 CORAL GABLES OFFICE 305.722.5721 4000 Ponce de Leon Blvd Suite 700 Coral Gables, FL 33146 FOLLOW US ON: Coral Gables Miami Beach LEAVE A MESSAGE First Name Last Name Email Address Phone Number Message By checking this box, I consent to receive text messages related

### JILLS-F007 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website — lists an office in: Coral Gables
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt labels a Coral Gables office and gives its address.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — narrow control from archived source-ID C3 evidence
- Evidence `jills-home-20260927/S1/E2` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [595, 1194):

  > Luxury Rentals Buyers Buy With Us Neighborhood Guides Relocation Sellers List With Us Our Numbers Marketing Masters Global Connections Industry Experts Distinctive Sales About Us The Jills Zeder Group Client Reviews In The Media Blog Press Videos Contact Us MIAMI BEACH OFFICE 305.341.7447 1682 Jefferson Avenue Miami Beach, FL 33139 CORAL GABLES OFFICE 305.722.5721 4000 Ponce de Leon Blvd Suite 700 Coral Gables, FL 33146 FOLLOW US ON: Coral Gables Miami Beach LEAVE A MESSAGE First Name Last Name Email Address Phone Number Message By checking this box, I consent to receive text messages related

### JILLS-F008 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website — displays a message form with fields for: name, email, phone number, and message
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: All four field labels are visible in the cited excerpt; the claim does not assert successful submission or delivery.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — narrow form-surface control from archived evidence
- Evidence `jills-home-20260927/S1/E2` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [595, 1194):

  > Luxury Rentals Buyers Buy With Us Neighborhood Guides Relocation Sellers List With Us Our Numbers Marketing Masters Global Connections Industry Experts Distinctive Sales About Us The Jills Zeder Group Client Reviews In The Media Blog Press Videos Contact Us MIAMI BEACH OFFICE 305.341.7447 1682 Jefferson Avenue Miami Beach, FL 33139 CORAL GABLES OFFICE 305.722.5721 4000 Ponce de Leon Blvd Suite 700 Coral Gables, FL 33146 FOLLOW US ON: Coral Gables Miami Beach LEAVE A MESSAGE First Name Last Name Email Address Phone Number Message By checking this box, I consent to receive text messages related

### JILLS-F009 — The Jills Zeder Group

- Candidate: The Jills Zeder Group — collects contact information via a form for: information requests and showing requests
- Proposed grade: **partial**
- Unsupported clause: collects contact information; information requests and showing requests
- Explanation: The cited excerpt shows fields and only the beginning of consent text; the request purposes continue in E3, and visible fields do not prove actual collection.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — archived atomic run C5 and AI-proposed review
- Evidence `jills-home-20260927/S1/E2` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [595, 1194):

  > Luxury Rentals Buyers Buy With Us Neighborhood Guides Relocation Sellers List With Us Our Numbers Marketing Masters Global Connections Industry Experts Distinctive Sales About Us The Jills Zeder Group Client Reviews In The Media Blog Press Videos Contact Us MIAMI BEACH OFFICE 305.341.7447 1682 Jefferson Avenue Miami Beach, FL 33139 CORAL GABLES OFFICE 305.722.5721 4000 Ponce de Leon Blvd Suite 700 Coral Gables, FL 33146 FOLLOW US ON: Coral Gables Miami Beach LEAVE A MESSAGE First Name Last Name Email Address Phone Number Message By checking this box, I consent to receive text messages related

### JILLS-F010 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website — shows SMS consent related to: information requests and showing requests
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The two cited contiguous spans preserve the complete consent statement and both purposes without claiming messages were sent.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — multi-reference consent control derived from archived split-sentence failure
- Evidence `jills-home-20260927/S1/E2` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [595, 1194):

  > Luxury Rentals Buyers Buy With Us Neighborhood Guides Relocation Sellers List With Us Our Numbers Marketing Masters Global Connections Industry Experts Distinctive Sales About Us The Jills Zeder Group Client Reviews In The Media Blog Press Videos Contact Us MIAMI BEACH OFFICE 305.341.7447 1682 Jefferson Avenue Miami Beach, FL 33139 CORAL GABLES OFFICE 305.722.5721 4000 Ponce de Leon Blvd Suite 700 Coral Gables, FL 33146 FOLLOW US ON: Coral Gables Miami Beach LEAVE A MESSAGE First Name Last Name Email Address Phone Number Message By checking this box, I consent to receive text messages related

- Evidence `jills-home-20260927/S1/E3` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [1195, 1754):

  > to information requests and showing requests from The Jills Zeder Group. You can reply "STOP" at any time to opt-out. Message and data rates may apply. Message frequency may vary. Text "HELP" for assistance. For more information, please visit our Privacy Policy and SMS Terms & Conditions Please prove you are human by selecting the tree . Submit Form Connect With Us Join Our VIP List Join Our VIP List Join our VIP list By checking this box, I consent to receive text messages related to information requests and showing requests from The Jills Zeder Group.

### JILLS-F011 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website — displays: a newsletter signup
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The excerpt explicitly says “Sign up” and identifies an exclusive newsletter.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — narrow control from archived atomic run C6 evidence
- Evidence `jills-home-20260927/S1/E13` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [6419, 6908):

  > Luxury Living Sign up for the latest lifestyle trends, market insights, and exclusive property updates. First Name Last Name Email Address Phone Number Message Stay in touch with The Jills Zeder exclusive newsletter. By checking this box, I consent to receive text messages related to information requests and showing requests from The Jills Zeder Group. You can reply "STOP" at any time to opt-out. Message and data rates may apply. Message frequency may vary. Text "HELP" for assistance.

### JILLS-F012 — The Jills Zeder Group

- Candidate: The Jills Zeder Group newsletter signup — offers updates about: lifestyle trends, market insights, and exclusive properties
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: All three content categories appear explicitly in the cited signup excerpt.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — archived atomic run C6; AI-proposed review marked span-supported
- Evidence `jills-home-20260927/S1/E13` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [6419, 6908):

  > Luxury Living Sign up for the latest lifestyle trends, market insights, and exclusive property updates. First Name Last Name Email Address Phone Number Message Stay in touch with The Jills Zeder exclusive newsletter. By checking this box, I consent to receive text messages related to information requests and showing requests from The Jills Zeder Group. You can reply "STOP" at any time to opt-out. Message and data rates may apply. Message frequency may vary. Text "HELP" for assistance.

### JILLS-F013 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website — says its listing marketing uses: digital, web, and social media
- Proposed grade: **supported**
- Unsupported clause: None proposed
- Explanation: The cited excerpt explicitly self-describes those three marketing channels and the claim preserves website attribution.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `supported_control` — narrow control from archived homepage evidence
- Evidence `jills-home-20260927/S1/E9` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [4403, 4838):

  > About Us THE POWER OF EXPERIENCE As the real estate market evolves, so do the strategies we use to market our luxury listings. We lead the industry in digital, web and social media marketing which enables us to consistently reach high-end buyers locally, nationally and globally. Client Reviews THE POWER OF INNOVATION Our innovative strategies and passion for client service have led to record sales and lifelong client relationships.

### JILLS-F014 — The Jills Zeder Group

- Candidate: The Jills Zeder Group website forms — trigger: automated lead follow-up in the team’s CRM
- Proposed grade: **unsupported**
- Unsupported clause: trigger automated lead follow-up in the team’s CRM
- Explanation: A signup surface and consent language do not establish a CRM, automation, successful submission, or follow-up workflow.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `deliberately_constructed_challenge` — form-to-workflow assumption built from saved Jills evidence
- Evidence `jills-home-20260927/S1/E13` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [6419, 6908):

  > Luxury Living Sign up for the latest lifestyle trends, market insights, and exclusive property updates. First Name Last Name Email Address Phone Number Message Stay in touch with The Jills Zeder exclusive newsletter. By checking this box, I consent to receive text messages related to information requests and showing requests from The Jills Zeder Group. You can reply "STOP" at any time to opt-out. Message and data rates may apply. Message frequency may vary. Text "HELP" for assistance.

### JILLS-F015 — The Jills Zeder Group

- Candidate: The Jills Zeder Group — offers property search, relocation assistance, and: digital marketing strategies for luxury listings
- Proposed grade: **unsupported**
- Unsupported clause: relocation assistance and digital marketing strategies for luxury listings
- Explanation: The cited span contains navigation labels and media coverage; it does not establish relocation assistance or the claimed digital-marketing service.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — archived source-ID run C5 and AI-proposed review
- Evidence `jills-home-20260927/S1/E10` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [4839, 5332):

  > List With Us Follow Us On Instagram @JILLSZEDERBEACH @JILLSZEDERGABLES Call To Actions NEIGHBORHOOD GUIDES Explore LUXURY CONDOS Explore PROPERTY SEARCH Explore In The Media The Jills Zeder Group is regularly featured in both national and local media, appearing in The Wall Street Journal, CNBC, Curbed, Forbes, Haute Living, Mansion Global, Miami Magazine, Ocean Drive magazine, Robb Report, South Florida Business Journal, The Real Deal, the Miami Herald, and the Sun Sentinel, among others.


## Discovery-question cases

### KERI-Q001 — Keri Shull Team

- Candidate: How does the team currently qualify and distribute incoming leads to its agents?
- Proposed grade: **unsupported**
- Unsupported clause: currently qualify and distribute incoming leads
- Explanation: Identity and marketing metrics do not establish incoming lead flow, qualification, or distribution.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — run 4686ade6e2f34706ae3161249d46a97e Q1
- Evidence `keri-home-20261005/S1/E1` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [0, 599):

  > Virginia, Maryland, & DC Real Estate Agents | Keri Shull Team Home Search Home Valuation Cities Contact Us menu About About Us Careers Giving Back Properties Featured Properties Past Transactions Arlington Properties Home Search Arlington Alexandria Washington DC Falls Church Vienna McLean Search All Homes Cities Discover Arlington Home Valuation Client Success Stories Guarantees Buyer Guarantee Seller Guarantee Move Up Guarantees Relocation Guarantees Mortgage Calculator Financing Options Press & Media Condos Blog All Blogs Lifestyle Blogs Real Estate Blogs Videos Contact Us My Search Portal

- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### KERI-Q002 — Keri Shull Team

- Candidate: What volume of off-market inventory is typically available at any given time?
- Proposed grade: **unsupported**
- Unsupported clause: off-market inventory is typically available
- Explanation: A historical share of off-market deals does not establish current off-market inventory or typical availability.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — run 4686ade6e2f34706ae3161249d46a97e Q2
- Evidence `keri-home-20261005/S1/E2` — https://kerishull.com/ — fetched 2026-10-05T16:45:04.517401+00:00 — offsets [600, 1188):

  > T: 703-609-5183 E: [email protected] The KS Team Selling Virginia, Maryland, & DC The KS Team Selling Virginia, Maryland, & DC Home Valuation join our team home search proven success 159,000+ Clients in our database that receive our newsletter & marketing campaigns $5B+ in sales volume 70K+ Followers on our social media platforms for The KS Team Over 22% of our deals were sold off-market At the KS Team, we believe that every client is special. Ranked as the Top Producing Real Estate Team in the DC Metro area, Keri Shull and her team have sold nearly $5 billion of local real estate.

### JILLS-Q001 — The Jills Zeder Group

- Candidate: How is lead intake from the website contact and newsletter forms integrated into the existing sales workflow?
- Proposed grade: **unsupported**
- Unsupported clause: integrated into the existing sales workflow
- Explanation: The pages show form surfaces but do not establish lead intake, integration, or an existing sales workflow.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — archived atomic run Q2
- Evidence `jills-home-20260927/S1/E2` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [595, 1194):

  > Luxury Rentals Buyers Buy With Us Neighborhood Guides Relocation Sellers List With Us Our Numbers Marketing Masters Global Connections Industry Experts Distinctive Sales About Us The Jills Zeder Group Client Reviews In The Media Blog Press Videos Contact Us MIAMI BEACH OFFICE 305.341.7447 1682 Jefferson Avenue Miami Beach, FL 33139 CORAL GABLES OFFICE 305.722.5721 4000 Ponce de Leon Blvd Suite 700 Coral Gables, FL 33146 FOLLOW US ON: Coral Gables Miami Beach LEAVE A MESSAGE First Name Last Name Email Address Phone Number Message By checking this box, I consent to receive text messages related

- Evidence `jills-home-20260927/S1/E13` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [6419, 6908):

  > Luxury Living Sign up for the latest lifestyle trends, market insights, and exclusive property updates. First Name Last Name Email Address Phone Number Message Stay in touch with The Jills Zeder exclusive newsletter. By checking this box, I consent to receive text messages related to information requests and showing requests from The Jills Zeder Group. You can reply "STOP" at any time to opt-out. Message and data rates may apply. Message frequency may vary. Text "HELP" for assistance.

### JILLS-Q002 — The Jills Zeder Group

- Candidate: Which CRM, if any, does the team use?
- Proposed grade: **neutral**
- Unsupported clause: None proposed
- Explanation: The wording asks about an unknown without assuming that a CRM exists.
- Status: `proposed_unreviewed`; authority: `ai_proposed`.
- Origin: `observed_agent_failure` — deliberately constructed neutral control
- Evidence `jills-home-20260927/S1/E7` — https://jillszeder.com/ — fetched 2026-09-27T14:10:48.266541+00:00 — offsets [3256, 3837):

  > The Jills® and The Zeder Team combining over four decades of experience, unparalleled expertise, and superior business savvy have come together to become The Jills Zeder Group, affiliated with Coldwell Banker Realty. The Jills Zeder Group is a powerhouse team of real estate experts specializing in the most magnificent properties in South Florida. And with their increased footprint, global reach, and worldwide marketing platform, The Jills Zeder Group has closed over $13 Billion worth of sales. Their combined track record speaks for itself: you are in extremely capable hands.
