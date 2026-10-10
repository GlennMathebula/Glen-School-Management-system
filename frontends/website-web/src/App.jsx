import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

const PUBLIC_LINKS = {
  applications: "/applications",
  careers: "/careers",
  studentPortal: "https://lms.glenmoniques.co.za",
};

const schools = [
  {
    title: "School of Retail & Business Management",
    icon: "▦",
    programmes: [
      "Retail Supervisor — NQF Level 4",
      "Small Retail Business Owner — NQF Level 4",
      "Checkout Operator — NQF Level 2",
      "Sales Assistant (General) — NQF Level 3",
      "Sales Representative — NQF Level 4",
      "New Venture Creation — NQF Level 2",
      "Small Business Consultant — NQF Level 5",
    ],
  },
  {
    title: "School of Education & Development",
    icon: "◎",
    programmes: [
      "Early Childhood Development Practitioner — NQF Level 4",
    ],
  },
  {
    title: "School of Health & Welfare",
    icon: "+",
    programmes: [
      "Social Counselling Worker — NQF Level 5",
      "Basic Emergency First Aid — NQF Level 2",
    ],
  },
  {
    title: "School of Services",
    icon: "◇",
    programmes: [
      "Commercial Cleaner — NQF Level 1",
    ],
  },
];

const shopCollections = [
  {
    name: "Corporate Polo Collection",
    school: "Glen Moniques Corporate",
    image: "/shop/corporate-polo.png",
    items: ["Corporate polo shirts", "Red, navy blue and white colourways", "Branded corporate apparel"],
    orderSubject: "Corporate Polo Collection",
  },
  {
    name: "School of Law Student T-Shirts",
    school: "School of Law",
    image: "/shop/school-law-tshirt.png",
    items: ["Student T-shirts", "Red, navy blue and white colourways", "Paralegal / legal-professional identity range"],
    orderSubject: "School of Law Student T-Shirt",
  },
  {
    name: "Retail & Business Merchandise",
    school: "School of Retail & Business Management",
    image: "/shop/retail-business-merch.png",
    items: ["Business polo shirts", "Bomber jackets and business apparel", "Travel mugs, bottles, bags, notebooks and accessories"],
    orderSubject: "Retail and Business Merchandise",
  },
  {
    name: "Education & Development Apparel",
    school: "School of Education & Development",
    image: "/shop/education-development-merch.png",
    items: ["Educator polo shirts", "Shirts, tunics and jackets", "Practical apparel and department wear"],
    orderSubject: "Education and Development Merchandise",
  },
  {
    name: "Health & Welfare Merchandise",
    school: "School of Health & Welfare",
    image: "/shop/health-welfare-merch.png",
    items: [
      "Scrub suits and healthcare coats",
      "Fleece jackets and medical backpacks",
      "Nurse watches, water bottles and travel mugs",
      "Tote bags, notebooks, lanyards, umbrellas and face masks",
      "First aid kits, blood pressure monitors, stethoscopes and infrared thermometers",
      "Hand sanitiser holders and reflective safety vests",
    ],
    orderSubject: "Health and Welfare Merchandise",
  },
  {
    name: "School of Services Merchandise",
    school: "School of Services",
    image: "/shop/school-services-merch.png",
    items: ["Service polo shirts", "Tunics, aprons and jackets", "Travel mugs, bottles, bags and stationery"],
    orderSubject: "School of Services Merchandise",
  },
];

const additionalMerch = [
  "Department T-Shirts",
  "Mugs & Travel Mugs",
  "Water Bottles",
  "Caps",
  "Hoodies & Jackets",
  "Backpacks & Tote Bags",
  "Laptop Bags",
  "Notebooks & Pen Sets",
  "Lanyards & ID Holders",
];

function merchMailto(subject = "Glen Moniques Merchandise Order") {
  const body = [
    "Hello Glen Moniques Shop,",
    "",
    `I would like to order/enquire about: ${subject}`,
    "",
    "Item / collection:",
    "Department / school:",
    "Colour:",
    "Size (if applicable):",
    "Quantity:",
    "Collection / delivery area:",
    "",
    "Name:",
    "Contact number:",
    "",
    "Official Glen Moniques slogan: HI TIRHELA N\'WINA",
    "",
    "Please confirm availability and send me the order details.",
  ].join("\\n");

  return `mailto:shop@glenmoniques.co.za?subject=${encodeURIComponent(
    `Merchandise Order - ${subject}`,
  )}&body=${encodeURIComponent(body)}`;
}

const faqs = [
  {
    q: "How do I apply to study at Glen Moniques?",
    a: "Use the Apply to Study button. It opens our learner enrolment application system where you can complete your application and upload the required documents.",
  },
  {
    q: "Where do registered students sign in?",
    a: "Registered students use the Student Portal at lms.glenmoniques.co.za. Your student number and login details are issued through the registration process.",
  },
  {
    q: "How do I apply for a job at Glen Moniques?",
    a: "Open Careers from the main menu. Careers and job applications are kept separate from learner enrolment applications.",
  },
  {
    q: "Are all programmes available during every intake?",
    a: "No. Programme availability, delivery mode, intake dates and funding arrangements can differ. Check the current programme information before applying.",
  },
];

function ExternalButton({ href, children, className = "" }) {
  return (
    <a className={`btn ${className}`} href={href}>
      {children}
    </a>
  );
}

function Header() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => setOpen(false), [location.pathname]);

  return (
    <header className="site-header">
      <a className="skip-link" href="#main">Skip to content</a>
      <div className="topbar">
        <div className="container topbar-inner">
          <span>GLEN MONIQUES (PTY) LTD</span>
          <div>
            <a href="tel:+27158802413">015 880 2413</a>
            <span>•</span>
            <a href="mailto:admin@glenmoniques.co.za">
              admin@glenmoniques.co.za
            </a>
          </div>
        </div>
      </div>

      <div className="container nav-wrap">
        <Link className="brand" to="/">
          <img src="/glen-moniques-logo.png" alt="Glen Moniques logo" />
          <div>
            <strong>GLEN MONIQUES</strong>
            <span>Skills • Education • Opportunity</span>
          </div>
        </Link>

        <button
          className="menu-button"
          aria-label="Toggle navigation"
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
        >
          ☰
        </button>

        <nav className={open ? "main-nav open" : "main-nav"}>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/programmes">Programmes</NavLink>
          <NavLink to="/shop">Shop</NavLink>
          <NavLink to="/admissions">Admissions</NavLink>
          <NavLink to="/about">About Us</NavLink>
          <NavLink to="/contact">Contact</NavLink>
          <a href={PUBLIC_LINKS.careers}>Careers</a>
          <ExternalButton href={PUBLIC_LINKS.applications} className="gold small">
            Apply Now
          </ExternalButton>
          <ExternalButton href={PUBLIC_LINKS.studentPortal} className="outline small">
            Student Portal
          </ExternalButton>
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div>
          <img className="footer-logo" src="/glen-moniques-logo.png" alt="" />
          <h3>Glen Moniques</h3>
          <p>
            Occupational and skills development programmes focused on practical
            learning, employability and community development.
          </p>
          <small>Company Registration: 2020/089305/07</small>
        </div>

        <div>
          <h4>Study</h4>
          <Link to="/programmes">Programmes</Link>
          <Link to="/shop">Glen Moniques Shop</Link>
          <Link to="/admissions">Admissions</Link>
          <a href={PUBLIC_LINKS.applications}>Apply to Study</a>
          <a href={PUBLIC_LINKS.studentPortal}>Student Portal</a>
        </div>

        <div>
          <h4>Glen Moniques</h4>
          <Link to="/about">About Us</Link>
          <a href={PUBLIC_LINKS.careers}>Careers</a>
          <Link to="/contact">Contact Us</Link>
          <Link to="/contact#complaints">Complaints & Enquiries</Link>
        </div>

        <div>
          <h4>Legal & Privacy</h4>
          <Link to="/terms">Terms & Conditions</Link>
          <Link to="/popia">Privacy & POPIA</Link>
          <Link to="/cookies">Cookie Policy</Link>
        </div>
      </div>

      <div className="container footer-bottom">
        <span>© {new Date().getFullYear()} Glen Moniques (Pty) Ltd.</span>
        <span>www.glenmoniques.co.za</span>
      </div>
    </footer>
  );
}

function CookieConsent() {
  const key = "gm_cookie_consent_v1";
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(!localStorage.getItem(key));
  }, []);

  function save(value) {
    localStorage.setItem(
      key,
      JSON.stringify({
        choice: value,
        updated_at: new Date().toISOString(),
      }),
    );
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <aside className="cookie-banner" aria-label="Cookie consent">
      <div>
        <strong>Your privacy matters</strong>
        <p>
          We use essential browser storage for site functionality and your
          cookie preference. Optional analytics should only be activated after
          consent. Read our <Link to="/cookies">Cookie Policy</Link>.
        </p>
      </div>
      <div className="cookie-actions">
        <button className="btn outline" onClick={() => save("essential")}>
          Essential Only
        </button>
        <button className="btn gold" onClick={() => save("all")}>
          Accept All
        </button>
      </div>
    </aside>
  );
}

function PageHero({ eyebrow, title, text, children }) {
  return (
    <section className="page-hero">
      <div className="container">
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{text}</p>
        {children}
      </div>
    </section>
  );
}

function Home() {
  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Welcome to Glen Moniques</span>
            <h1>Build skills. Create opportunity. Move forward.</h1>
            <p>
              Career-focused occupational and skills development programmes
              designed to support learners, businesses and communities.
            </p>
            <div className="hero-actions">
              <ExternalButton href={PUBLIC_LINKS.applications} className="gold">
                Apply to Study
              </ExternalButton>
              <Link className="btn light" to="/programmes">
                Explore Programmes
              </Link>
              <ExternalButton href={PUBLIC_LINKS.studentPortal} className="outline">
                Student Portal
              </ExternalButton>
            </div>

            <div className="hero-meta">
              <div>
                <strong>Occupational learning</strong>
                <span>Knowledge, practical and workplace-focused training</span>
              </div>
              <div>
                <strong>Student support</strong>
                <span>Applications, registration, learning and assessment support</span>
              </div>
            </div>
          </div>

          <div className="hero-card">
            <img src="/glen-moniques-logo.png" alt="" />
            <span>GLEN MONIQUES</span>
            <h2>Your next step starts here.</h2>
            <p>
              Apply for a programme, access your student portal or explore
              employment opportunities.
            </p>
            <div className="stacked-actions">
              <a href={PUBLIC_LINKS.applications}>Apply to Study <b>→</b></a>
              <a href={PUBLIC_LINKS.careers}>Careers & Job Applications <b>→</b></a>
              <a href={PUBLIC_LINKS.studentPortal}>Student Portal <b>→</b></a>
            </div>
          </div>
        </div>
      </section>

      <section className="quick-access">
        <div className="container quick-grid">
          <a className="quick-card" href={PUBLIC_LINKS.applications}>
            <span>01</span>
            <h3>Apply to Study</h3>
            <p>Submit your learner enrolment application online.</p>
            <b>Open Applications →</b>
          </a>
          <a className="quick-card" href={PUBLIC_LINKS.careers}>
            <span>02</span>
            <h3>Careers</h3>
            <p>View Glen Moniques vacancies and submit a job application.</p>
            <b>View Careers →</b>
          </a>
          <a className="quick-card" href={PUBLIC_LINKS.studentPortal}>
            <span>03</span>
            <h3>Student Portal</h3>
            <p>Access learning, results, documents, finance and student services.</p>
            <b>Sign In →</b>
          </a>
          <Link className="quick-card" to="/contact">
            <span>04</span>
            <h3>Need Help?</h3>
            <p>Speak to our team about applications, programmes or support.</p>
            <b>Contact Us →</b>
          </Link>
        </div>
      </section>

      <section className="section">
        <div className="container section-head">
          <div>
            <span className="eyebrow dark">Our Schools</span>
            <h2>Programmes organised around real learning pathways.</h2>
          </div>
          <Link className="text-link" to="/programmes">View all programmes →</Link>
        </div>

        <div className="container school-grid">
          {schools.map((school) => (
            <article className="school-card" key={school.title}>
              <div className="school-icon">{school.icon}</div>
              <h3>{school.title}</h3>
              <ul>
                {school.programmes.slice(0, 3).map((programme) => (
                  <li key={programme}>{programme}</li>
                ))}
              </ul>
              {school.programmes.length > 3 && (
                <small>+ {school.programmes.length - 3} more programme(s)</small>
              )}
            </article>
          ))}
        </div>
      </section>

      <section className="section alt">
        <div className="container split">
          <div>
            <span className="eyebrow dark">About Glen Moniques</span>
            <h2>Learning that connects education with work and enterprise.</h2>
            <p className="lead">
              Glen Moniques is a South African skills development provider
              serving learners and organisations through occupational,
              skills-based and workplace-focused learning.
            </p>
            <p>
              Our approach combines structured learning, learner support and
              practical implementation so that training is connected to real
              outcomes.
            </p>
            <Link className="btn navy" to="/about">Learn More About Us</Link>
          </div>
          <div className="feature-panel">
            <div>
              <span>✓</span>
              <strong>Programme-focused support</strong>
              <p>From application and registration through learning and assessment.</p>
            </div>
            <div>
              <span>✓</span>
              <strong>Digital student services</strong>
              <p>Secure online access to important learner information and services.</p>
            </div>
            <div>
              <span>✓</span>
              <strong>Employer and community orientation</strong>
              <p>Training designed around practical skills and workplace relevance.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container center-head">
          <span className="eyebrow dark">Admissions</span>
          <h2>Four simple steps to start your application.</h2>
        </div>
        <div className="container steps-grid">
          {[
            ["1", "Choose a programme", "Review available programmes and entry requirements."],
            ["2", "Apply online", "Complete the learner enrolment application and provide your details."],
            ["3", "Upload documents", "Submit the documents requested for your chosen programme."],
            ["4", "Admissions review", "Our team reviews the application and communicates the outcome."],
          ].map(([number, title, text]) => (
            <article className="step-card" key={number}>
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
        <div className="center-action">
          <ExternalButton href={PUBLIC_LINKS.applications} className="gold">
            Start Your Application
          </ExternalButton>
        </div>
      </section>

      <section className="section navy-section">
        <div className="container cta-grid">
          <div>
            <span className="eyebrow">Already registered?</span>
            <h2>Your learning services are one sign-in away.</h2>
            <p>
              Use the Student Portal for modules, results, timetable,
              documents, finance, student card services and communication.
            </p>
          </div>
          <ExternalButton href={PUBLIC_LINKS.studentPortal} className="gold">
            Open Student Portal
          </ExternalButton>
        </div>
      </section>

      <section className="section shop-home">
        <div className="container shop-home-grid">
          <div className="shop-home-copy">
            <span className="eyebrow dark">Glen Moniques Shop</span>
            <h2>Wear your school. Carry the brand.</h2>
            <p>
              Explore Glen Moniques branded T-shirts, polos, mugs, bags,
              drinkware, stationery and department merchandise. Prices are not
              displayed online - email our shop for availability and order
              confirmation.
            </p>
            <div className="hero-actions">
              <Link className="btn navy" to="/shop">Visit the Shop</Link>
              <a className="btn outline-dark" href={merchMailto()}>
                Email shop@glenmoniques.co.za
              </a>
            </div>
          </div>
          <div className="shop-home-preview">
            <img
              src="/shop/corporate-polo.png"
              alt="Glen Moniques corporate polo collection"
            />
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container center-head">
          <span className="eyebrow dark">Frequently Asked Questions</span>
          <h2>Quick answers before you get started.</h2>
        </div>
        <div className="container faq-grid">
          {faqs.map((item) => (
            <details className="faq" key={item.q}>
              <summary>{item.q}</summary>
              <p>{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      <ContactStrip />
    </>
  );
}

function Programmes() {
  return (
    <>
      <PageHero
        eyebrow="Study at Glen Moniques"
        title="Schools & Programmes"
        text="Explore our occupational and skills development pathways. Programme availability can vary by intake."
      >
        <ExternalButton href={PUBLIC_LINKS.applications} className="gold">
          Apply to Study
        </ExternalButton>
      </PageHero>

      <section className="section">
        <div className="container programme-grid">
          {schools.map((school) => (
            <article className="programme-school" key={school.title}>
              <div className="school-icon">{school.icon}</div>
              <h2>{school.title}</h2>
              <div className="programme-list">
                {school.programmes.map((programme) => (
                  <div key={programme}>
                    <span>Programme</span>
                    <strong>{programme}</strong>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
        <div className="container note-box">
          <strong>Important:</strong> Entry requirements, accreditation status,
          delivery mode, funding arrangements and intake dates should be
          confirmed for the specific programme before enrolment.
        </div>
      </section>
    </>
  );
}

function Admissions() {
  return (
    <>
      <PageHero
        eyebrow="Admissions"
        title="Apply to study with Glen Moniques"
        text="Our learner application system is separate from Careers. Use it only when applying to enrol in a programme."
      >
        <ExternalButton href={PUBLIC_LINKS.applications} className="gold">
          Open Enrolment Application
        </ExternalButton>
      </PageHero>

      <section className="section">
        <div className="container split admissions-split">
          <div>
            <h2>Before you apply</h2>
            <p>
              Have your personal information, education history, contact
              details and supporting documents ready. The exact supporting
              documents may differ by programme or funded project.
            </p>
            <ul className="check-list">
              <li>Choose the correct programme and intake.</li>
              <li>Use accurate personal and contact information.</li>
              <li>Upload clear, readable supporting documents.</li>
              <li>Review POPIA consent before submitting.</li>
              <li>Keep your application acknowledgement for reference.</li>
            </ul>
          </div>
          <div className="info-card">
            <span className="eyebrow dark">Application systems</span>
            <h3>Study vs Employment</h3>
            <p>
              <b>Study application:</b> use the learner enrolment application.
            </p>
            <a className="btn gold full" href={PUBLIC_LINKS.applications}>
              Apply to Study
            </a>
            <p>
              <b>Job application:</b> use the Careers portal.
            </p>
            <a className="btn outline-dark full" href={PUBLIC_LINKS.careers}>
              View Careers
            </a>
          </div>
        </div>
      </section>

      <ContactStrip />
    </>
  );
}

function About() {
  return (
    <>
      <PageHero
        eyebrow="About Us"
        title="Education, skills and opportunity."
        text="Glen Moniques (Pty) Ltd is a South African skills development provider focused on occupational learning, practical capability and learner support."
      />

      <section className="section">
        <div className="container split">
          <div>
            <h2>What we do</h2>
            <p className="lead">
              We support learners and organisations through structured
              programmes that connect knowledge, practical learning and
              workplace or enterprise outcomes.
            </p>
            <p>
              Our services include learner recruitment and admissions,
              programme delivery, assessment support, student administration,
              employer collaboration and digital learner services.
            </p>
          </div>
          <div className="values-grid">
            <article><strong>Access</strong><p>Make learning pathways clear and reachable.</p></article>
            <article><strong>Quality</strong><p>Deliver structured and accountable learning services.</p></article>
            <article><strong>Practicality</strong><p>Connect learning with real work and enterprise needs.</p></article>
            <article><strong>Support</strong><p>Guide learners through the full learning journey.</p></article>
          </div>
        </div>
      </section>

      <section className="section alt">
        <div className="container center-head">
          <span className="eyebrow dark">Our Digital Ecosystem</span>
          <h2>One organisation, clear pathways for every user.</h2>
        </div>
        <div className="container ecosystem-grid">
          <div><b>Public Website</b><span>Information, programmes and policies</span></div>
          <div><b>Applications</b><span>Learner enrolment applications</span></div>
          <div><b>Careers</b><span>Vacancies and employment applications</span></div>
          <div><b>Student Portal</b><span>Learning and student self-service</span></div>
        </div>
      </section>

      <ContactStrip />
    </>
  );
}

function Shop() {
  return (
    <>
      <PageHero
        eyebrow="Glen Moniques Shop"
        title="Branded merchandise for the Glen Moniques community."
        text="Shop T-shirts, polos, mugs, drinkware, bags, stationery and department merchandise. No prices are displayed online. Email our shop to request availability and place an order."
      >
        <a className="btn gold" href={merchMailto()}>
          Order via shop@glenmoniques.co.za
        </a>
      </PageHero>

      <section className="shop-slogan-strip">
        <div className="container shop-slogan-inner">
          <span>OFFICIAL GLEN MONIQUES SLOGAN</span>
          <strong>HI TIRHELA N'WINA</strong>
          <p>
            All official Glen Moniques Shop branding and future merchandise
            should use this slogan. Some earlier concept artwork may still show
            older wording.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container shop-intro">
          <div>
            <span className="eyebrow dark">Featured Collections</span>
            <h2>Our merchandise collections</h2>
            <p>
              These collections use Glen Moniques branding and department
              identities. Select a collection and email the shop with the item,
              colour, size and quantity you need.
            </p>
          </div>
          <div className="shop-order-box">
            <strong>How to order</strong>
            <ol>
              <li>Choose the merchandise or collection.</li>
              <li>Email your size, colour and quantity where applicable.</li>
              <li>Include your name, contact number and collection/delivery area.</li>
              <li>Our shop will confirm availability and the order details.</li>
            </ol>
            <a className="btn gold full" href={merchMailto()}>
              Start an Email Order
            </a>
          </div>
        </div>

        <div className="container merch-grid">
          {shopCollections.map((collection) => (
            <article className="merch-card" key={collection.name}>
              <button
                className="merch-image"
                type="button"
                onClick={() => window.open(collection.image, "_blank")}
                aria-label={`View ${collection.name} design`}
              >
                <img src={collection.image} alt={collection.name} />
              </button>
              <div className="merch-card-body">
                <span>{collection.school}</span>
                <h3>{collection.name}</h3>
                <ul>
                  {collection.items.map((item) => <li key={item}>{item}</li>)}
                </ul>
                <a className="btn navy full" href={merchMailto(collection.orderSubject)}>
                  Order / Enquire by Email
                </a>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section alt">
        <div className="container center-head">
          <span className="eyebrow dark">More Glen Moniques Merch</span>
          <h2>Other merchandise you can enquire about</h2>
          <p className="shop-subtext">
            Availability can vary. Email the shop and our team will confirm the
            options available for your department or order.
          </p>
        </div>

        <div className="container merch-chip-grid">
          {additionalMerch.map((item) => (
            <a key={item} href={merchMailto(item)} className="merch-chip">
              <span>GM</span>
              <strong>{item}</strong>
              <b>Enquire →</b>
            </a>
          ))}
        </div>
      </section>

      <section className="section shop-departments">
        <div className="container split">
          <div>
            <span className="eyebrow dark">Department Merchandise</span>
            <h2>Represent your school or department.</h2>
            <p className="lead">
              Department-branded T-shirts and apparel can be ordered or
              requested through the Glen Moniques Shop.
            </p>
            <p>
              When ordering, tell us which school or department you need so the
              shop can confirm the correct design, colours and available sizes.
            </p>
          </div>
          <div className="department-merch-list">
            <div><span>RBM</span><b>Retail & Business Management</b></div>
            <div><span>ED</span><b>Education & Development</b></div>
            <div><span>HW</span><b>Health & Welfare — Scrubs & Care Merchandise</b></div>
            <div><span>SV</span><b>School of Services</b></div>
            <div><span>LAW</span><b>School of Law</b></div>
          </div>
        </div>
      </section>

      <section className="contact-strip shop-contact">
        <div className="container cta-grid">
          <div>
            <span className="eyebrow">Merchandise Orders</span>
            <h2>Ready to order?</h2>
            <p>
              Email shop@glenmoniques.co.za with your selected item, size,
              colour and quantity. The shop will reply with availability and
              order information.
            </p>
          </div>
          <a className="btn gold" href={merchMailto()}>
            Email the Shop
          </a>
        </div>
      </section>
    </>
  );
}

function Contact() {
  return (
    <>
      <PageHero
        eyebrow="Contact Us"
        title="Speak to the Glen Moniques team"
        text="Contact us for programme enquiries, applications, student support or general information."
      />

      <section className="section">
        <div className="container contact-grid">
          <article>
            <span>Email</span>
            <h3>admin@glenmoniques.co.za</h3>
            <a href="mailto:admin@glenmoniques.co.za">Send Email →</a>
          </article>
          <article>
            <span>Telephone</span>
            <h3>015 880 2413</h3>
            <a href="tel:+27158802413">Call Us →</a>
          </article>
          <article>
            <span>Website</span>
            <h3>www.glenmoniques.co.za</h3>
            <a href="https://www.glenmoniques.co.za">Visit Website →</a>
          </article>
          <article>
            <span>Location</span>
            <h3>Limpopo, South Africa</h3>
            <p>Contact our office for visit and appointment information.</p>
          </article>
        </div>

        <div className="container support-panel" id="complaints">
          <div>
            <span className="eyebrow dark">Complaints & Enquiries</span>
            <h2>Need help resolving an issue?</h2>
            <p>
              Send a clear description of your concern, your full name and any
              relevant application or student reference number to our
              administration team.
            </p>
          </div>
          <a className="btn navy" href="mailto:admin@glenmoniques.co.za">
            Contact Administration
          </a>
        </div>
      </section>
    </>
  );
}

function Terms() {
  return (
    <LegalPage title="Terms & Conditions" updated="2 October 2026">
      <h2>1. Website use</h2>
      <p>
        This website provides information about Glen Moniques, its programmes,
        services, learner applications and careers. You must use the website
        lawfully and must not attempt to interfere with its security or
        availability.
      </p>

      <h2>2. Programme information</h2>
      <p>
        Programme availability, entry requirements, delivery arrangements,
        fees, funding and intake dates may change. Information on this website
        should be confirmed against the current programme and enrolment
        documentation before a final commitment is made.
      </p>

      <h2>3. Applications and admissions</h2>
      <p>
        Submitting an application does not itself guarantee admission,
        registration or funding. Admission remains subject to programme
        requirements, available capacity, required documentation and the
        applicable admissions process.
      </p>

      <h2>4. Fees and payments</h2>
      <p>
        Where fees apply, the amount, payment schedule, deposits, cancellation
        terms and refund rules should be set out in the applicable quotation,
        enrolment agreement, invoice or funding arrangement.
      </p>

      <h2>5. Accounts and security</h2>
      <p>
        Users are responsible for protecting their login credentials and for
        notifying Glen Moniques if they suspect unauthorised access to their
        account.
      </p>

      <h2>6. Intellectual property</h2>
      <p>
        Unless stated otherwise, Glen Moniques owns or lawfully uses the
        website content, branding, learning-system interfaces and related
        materials. Content may not be reproduced or redistributed unlawfully.
      </p>

      <h2>7. External services</h2>
      <p>
        The website may link to external platforms or services. Those services
        may have their own terms and privacy practices.
      </p>

      <h2>8. Contact</h2>
      <p>
        Questions about these terms may be sent to{" "}
        <a href="mailto:admin@glenmoniques.co.za">admin@glenmoniques.co.za</a>.
      </p>
    </LegalPage>
  );
}

function Popia() {
  return (
    <LegalPage title="Privacy Notice & POPIA" updated="2 October 2026">
      <p className="legal-intro">
        This notice explains, at a website level, how Glen Moniques may collect
        and use personal information. Operational privacy procedures and
        formal internal policies may contain additional detail.
      </p>

      <h2>1. Information we may collect</h2>
      <p>
        Depending on the service used, this may include identity information,
        contact details, education history, employment information, application
        information, programme records, uploaded documents, payment-related
        records, communication records and technical information required to
        operate our systems.
      </p>

      <h2>2. Why information is processed</h2>
      <p>
        Personal information may be processed to manage applications,
        admissions, learner registration, programme delivery, assessment,
        student services, finance, communication, recruitment, reporting,
        legal obligations, security and administration.
      </p>

      <h2>3. Sharing of information</h2>
      <p>
        Information may be shared with authorised staff, service providers,
        employers or workplace partners, regulators, quality assurance bodies,
        funders or other parties where this is necessary and lawful for the
        relevant programme or service.
      </p>

      <h2>4. Security and retention</h2>
      <p>
        Glen Moniques should use reasonable technical and organisational
        safeguards appropriate to the information processed. Records should be
        retained only for as long as required for operational, contractual,
        regulatory or legal purposes.
      </p>

      <h2>5. Your privacy rights</h2>
      <p>
        Subject to applicable law, you may request access to personal
        information held about you, ask for inaccurate information to be
        corrected, raise an objection in appropriate circumstances or enquire
        about how your information is processed.
      </p>

      <h2>6. Privacy enquiries</h2>
      <p>
        Privacy enquiries and requests may be sent to{" "}
        <a href="mailto:admin@glenmoniques.co.za">admin@glenmoniques.co.za</a>.
        Identity verification may be required before personal records are
        released or changed.
      </p>
    </LegalPage>
  );
}

function Cookies() {
  const [saved, setSaved] = useState("");

  function update(choice) {
    localStorage.setItem(
      "gm_cookie_consent_v1",
      JSON.stringify({
        choice,
        updated_at: new Date().toISOString(),
      }),
    );
    setSaved(choice);
  }

  return (
    <LegalPage title="Cookie Policy" updated="2 October 2026">
      <p className="legal-intro">
        This website currently uses browser storage for essential functionality
        and for remembering your cookie preference. Optional tracking should
        not be activated unless an appropriate consent mechanism is in place.
      </p>

      <h2>Essential storage</h2>
      <p>
        Essential storage may be used to remember security, session,
        navigation or consent information needed for website functionality.
        Essential storage cannot always be disabled without affecting the
        service.
      </p>

      <h2>Analytics</h2>
      <p>
        If analytics are introduced, they should be configured in accordance
        with the selected consent preference and described in this policy.
      </p>

      <h2>Managing your preference</h2>
      <p>
        You can update the preference saved by this website below. Browser
        settings may also allow you to delete stored site data.
      </p>

      <div className="legal-actions">
        <button className="btn outline-dark" onClick={() => update("essential")}>
          Use Essential Only
        </button>
        <button className="btn gold" onClick={() => update("all")}>
          Accept All
        </button>
      </div>
      {saved && <p className="saved-note">Preference saved: {saved}.</p>}
    </LegalPage>
  );
}

function LegalPage({ title, updated, children }) {
  return (
    <>
      <PageHero
        eyebrow="Legal & Privacy"
        title={title}
        text={`Last updated: ${updated}`}
      />
      <section className="section">
        <article className="container legal-content">{children}</article>
      </section>
    </>
  );
}

function ContactStrip() {
  return (
    <section className="contact-strip">
      <div className="container cta-grid">
        <div>
          <span className="eyebrow">Need assistance?</span>
          <h2>Talk to our team before you apply.</h2>
          <p>
            We can help with programme information, application questions and
            student support.
          </p>
        </div>
        <Link className="btn gold" to="/contact">Contact Us</Link>
      </div>
    </section>
  );
}

function NotFound() {
  return (
    <section className="not-found">
      <div className="container">
        <span>404</span>
        <h1>Page not found</h1>
        <p>The page you requested is not available.</p>
        <Link className="btn gold" to="/">Return Home</Link>
      </div>
    </section>
  );
}

export default function App() {
  const location = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [location.pathname]);

  return (
    <div className="site-shell">
      <Header />
      <main id="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/programmes" element={<Programmes />} />
          <Route path="/shop" element={<Shop />} />
          <Route path="/admissions" element={<Admissions />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/popia" element={<Popia />} />
          <Route path="/cookies" element={<Cookies />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      <CookieConsent />
    </div>
  );
}
