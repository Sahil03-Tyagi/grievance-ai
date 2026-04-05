INSERT INTO departments 
  (category, city, authority_name, email, sla_days, escalation_authority_email)
VALUES
  ('electricity','Ghaziabad','UP Power Corporation Ltd',
   'cgm.gzb@uppclonline.com',7,'ombudsman.electricity.up@gov.in'),
  ('electricity','Delhi','BSES Rajdhani Power Ltd',
   'grievance@bsesdelhi.com',7,'ombudsman.delhi.electricity@gov.in'),
  ('water','Ghaziabad','Jal Nigam Ghaziabad',
   'ee.gzb@jalnigramup.org',10,'md.jalnigam.up@gov.in'),
  ('water','Delhi','Delhi Jal Board',
   'ceo@delhijalboard.nic.in',10,'grievance.djb@delhi.gov.in'),
  ('road','Ghaziabad','Ghaziabad Municipal Corporation',
   'commissioner@gmconline.in',15,'secretary.pwd.up@gov.in'),
  ('road','Delhi','PWD Delhi',
   'se.pwd@delhi.gov.in',15,'chiefengineer.pwd@delhi.gov.in'),
  ('pension','Uttar Pradesh','EPFO Regional Office Noida',
   'ro.noida@epfindia.gov.in',14,'cpfc@epfindia.gov.in'),
  ('pension','Delhi','EPFO Regional Office Delhi',
   'ro.delhi@epfindia.gov.in',14,'cpfc@epfindia.gov.in'),
  ('police','Ghaziabad','SSP Ghaziabad',
   'ssp.gzb@uppolice.gov.in',7,'adgzone.merrut@uppolice.gov.in'),
  ('police','Delhi','DCP Delhi',
   'dcp.hq@delhipolice.gov.in',7,'commissionerate@delhipolice.gov.in'),
  ('sanitation','Ghaziabad','GMC Sanitation Dept',
   'sanitation@gmconline.in',7,'commissioner@gmconline.in'),
  ('gas','Uttar Pradesh','Indane LPG UP',
   'customercare.up@indianoil.in',10,'nodal.lpg@indianoil.in'),
  ('telecom','India','BSNL Grievance Cell',
   'pgm.bb@bsnl.co.in',10,'nodalofficer.bsnl@dot.gov.in'),
  ('railway','India','Indian Railways CPGRAMS',
   'gm.nr@indianrailways.gov.in',14,'chairmanrailwayboard@gov.in'),
  ('banking','India','RBI Banking Ombudsman',
   'crpc@rbi.org.in',30,'ombudsman.rbi@rbi.org.in');

INSERT INTO precedents 
  (category, location, issue_summary, resolution, days_taken)
VALUES
  ('electricity','Ghaziabad',
   'Power cut for 2 weeks, no response from DISCOM',
   'Escalated to ombudsman, connection restored in 3 days',8),
  ('electricity','Delhi',
   'Incorrect electricity bill, overcharged by 5x',
   'Complaint filed with BSES, bill corrected within 10 days',10),
  ('water','Ghaziabad',
   'No water supply for 10 days in residential colony',
   'Jal Nigam responded after formal complaint, supply restored',7),
  ('pension','Uttar Pradesh',
   'Senior citizen pension not received for 3 months',
   'EPFO corrected bank details, pension credited',12),
  ('road','Ghaziabad',
   'Large pothole causing accidents on main road for 4 months',
   'GMC repaired after escalation to Municipal Commissioner',18),
  ('police','Delhi',
   'FIR not registered despite multiple visits to station',
   'DCP intervention resulted in FIR filing within 24 hours',3),
  ('electricity','Ghaziabad',
   'New electricity connection applied 2 months ago, no action',
   'UPPCL issued connection after consumer forum notice',21),
  ('water','Delhi',
   'Contaminated water supply causing illness in area',
   'DJB emergency team deployed, supply fixed same day',1),
  ('pension','Delhi',
   'PF withdrawal stuck for 6 months',
   'EPFO Delhi processed after RTI filing',25),
  ('road','Delhi',
   'Broken footpath causing falls for elderly residents',
   'PWD repaired after MLA intervention requested by system',14);

-- Generate embeddings for precedents (run after seeding)
UPDATE precedents 
SET embedding = embedding('text-embedding-005', 
  category || ' ' || location || ' ' || issue_summary)::vector
WHERE embedding IS NULL;