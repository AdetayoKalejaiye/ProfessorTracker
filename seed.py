from app import app, db
from models import Professor

PROFESSORS = [
    # MIT - Cambridge, MA
    {"name": "James Anderson", "university": "MIT", "department": "Computer Science", "email": "j.anderson@mit.edu", "interests": "Machine Learning, Neural Networks, Computer Vision", "city": "Cambridge", "state": "MA", "latitude": 42.3601, "longitude": -71.0942},
    {"name": "Sarah Chen", "university": "MIT", "department": "Electrical Engineering", "email": "s.chen@mit.edu", "interests": "Quantum Computing, Photonics, Signal Processing", "city": "Cambridge", "state": "MA", "latitude": 42.3601, "longitude": -71.0942},
    {"name": "Robert Kim", "university": "MIT", "department": "Physics", "email": "r.kim@mit.edu", "interests": "Condensed Matter Physics, Superconductivity, Quantum Materials", "city": "Cambridge", "state": "MA", "latitude": 42.3601, "longitude": -71.0942},
    {"name": "Emily Watson", "university": "MIT", "department": "Mathematics", "email": "e.watson@mit.edu", "interests": "Algebraic Topology, Category Theory, Homological Algebra", "city": "Cambridge", "state": "MA", "latitude": 42.3601, "longitude": -71.0942},
    # Stanford - Stanford, CA
    {"name": "Michael Torres", "university": "Stanford", "department": "Computer Science", "email": "m.torres@stanford.edu", "interests": "Natural Language Processing, Large Language Models, AI Safety", "city": "Stanford", "state": "CA", "latitude": 37.4275, "longitude": -122.1697},
    {"name": "Jessica Park", "university": "Stanford", "department": "Biology", "email": "j.park@stanford.edu", "interests": "Genomics, CRISPR, Synthetic Biology", "city": "Stanford", "state": "CA", "latitude": 37.4275, "longitude": -122.1697},
    {"name": "David Liu", "university": "Stanford", "department": "Neuroscience", "email": "d.liu@stanford.edu", "interests": "Neural Circuits, Memory, Optogenetics", "city": "Stanford", "state": "CA", "latitude": 37.4275, "longitude": -122.1697},
    {"name": "Amanda Foster", "university": "Stanford", "department": "Economics", "email": "a.foster@stanford.edu", "interests": "Behavioral Economics, Game Theory, Market Design", "city": "Stanford", "state": "CA", "latitude": 37.4275, "longitude": -122.1697},
    # Harvard - Cambridge, MA
    {"name": "Thomas Wright", "university": "Harvard", "department": "Physics", "email": "t.wright@harvard.edu", "interests": "Astrophysics, Dark Matter, Cosmology", "city": "Cambridge", "state": "MA", "latitude": 42.3770, "longitude": -71.1167},
    {"name": "Rachel Green", "university": "Harvard", "department": "Chemistry", "email": "r.green@harvard.edu", "interests": "Organic Chemistry, Drug Discovery, Protein Engineering", "city": "Cambridge", "state": "MA", "latitude": 42.3770, "longitude": -71.1167},
    {"name": "Kevin Zhang", "university": "Harvard", "department": "Computer Science", "email": "k.zhang@harvard.edu", "interests": "Distributed Systems, Cryptography, Blockchain", "city": "Cambridge", "state": "MA", "latitude": 42.3770, "longitude": -71.1167},
    {"name": "Laura Martinez", "university": "Harvard", "department": "Psychology", "email": "l.martinez@harvard.edu", "interests": "Cognitive Psychology, Decision Making, Social Cognition", "city": "Cambridge", "state": "MA", "latitude": 42.3770, "longitude": -71.1167},
    # Carnegie Mellon - Pittsburgh, PA
    {"name": "Daniel Brooks", "university": "Carnegie Mellon", "department": "Computer Science", "email": "d.brooks@cmu.edu", "interests": "Robotics, Computer Vision, Autonomous Systems", "city": "Pittsburgh", "state": "PA", "latitude": 40.4433, "longitude": -79.9436},
    {"name": "Nicole Adams", "university": "Carnegie Mellon", "department": "Data Science", "email": "n.adams@cmu.edu", "interests": "Statistical Learning, Data Mining, Predictive Analytics", "city": "Pittsburgh", "state": "PA", "latitude": 40.4433, "longitude": -79.9436},
    {"name": "Steven Clark", "university": "Carnegie Mellon", "department": "Electrical Engineering", "email": "s.clark@cmu.edu", "interests": "VLSI Design, Embedded Systems, IoT", "city": "Pittsburgh", "state": "PA", "latitude": 40.4433, "longitude": -79.9436},
    # UC Berkeley - Berkeley, CA
    {"name": "Michelle Lee", "university": "UC Berkeley", "department": "Computer Science", "email": "m.lee@berkeley.edu", "interests": "Operating Systems, Cloud Computing, Distributed Systems", "city": "Berkeley", "state": "CA", "latitude": 37.8724, "longitude": -122.2595},
    {"name": "Christopher Wang", "university": "UC Berkeley", "department": "Mathematics", "email": "c.wang@berkeley.edu", "interests": "Number Theory, Cryptography, Algebraic Geometry", "city": "Berkeley", "state": "CA", "latitude": 37.8724, "longitude": -122.2595},
    {"name": "Stephanie Brown", "university": "UC Berkeley", "department": "Physics", "email": "s.brown@berkeley.edu", "interests": "Particle Physics, High Energy Physics, Accelerator Science", "city": "Berkeley", "state": "CA", "latitude": 37.8724, "longitude": -122.2595},
    {"name": "Andrew Davis", "university": "UC Berkeley", "department": "Economics", "email": "a.davis@berkeley.edu", "interests": "Labor Economics, Econometrics, Public Policy", "city": "Berkeley", "state": "CA", "latitude": 37.8724, "longitude": -122.2595},
    # Caltech - Pasadena, CA
    {"name": "Patricia Wilson", "university": "Caltech", "department": "Physics", "email": "p.wilson@caltech.edu", "interests": "Gravitational Waves, Black Holes, General Relativity", "city": "Pasadena", "state": "CA", "latitude": 34.1377, "longitude": -118.1253},
    {"name": "Brian Johnson", "university": "Caltech", "department": "Chemistry", "email": "b.johnson@caltech.edu", "interests": "Computational Chemistry, Molecular Dynamics, Quantum Chemistry", "city": "Pasadena", "state": "CA", "latitude": 34.1377, "longitude": -118.1253},
    {"name": "Jennifer Moore", "university": "Caltech", "department": "Biology", "email": "j.moore@caltech.edu", "interests": "Structural Biology, Protein Folding, Cryo-EM", "city": "Pasadena", "state": "CA", "latitude": 34.1377, "longitude": -118.1253},
    # Princeton - Princeton, NJ
    {"name": "Mark Thompson", "university": "Princeton", "department": "Mathematics", "email": "m.thompson@princeton.edu", "interests": "Topology, Differential Geometry, Mathematical Physics", "city": "Princeton", "state": "NJ", "latitude": 40.3573, "longitude": -74.6672},
    {"name": "Susan Harris", "university": "Princeton", "department": "Computer Science", "email": "s.harris@princeton.edu", "interests": "Algorithms, Complexity Theory, Computational Geometry", "city": "Princeton", "state": "NJ", "latitude": 40.3573, "longitude": -74.6672},
    {"name": "Paul Robinson", "university": "Princeton", "department": "Economics", "email": "p.robinson@princeton.edu", "interests": "Macroeconomics, International Trade, Development Economics", "city": "Princeton", "state": "NJ", "latitude": 40.3573, "longitude": -74.6672},
    # Yale - New Haven, CT
    {"name": "Nancy White", "university": "Yale", "department": "Neuroscience", "email": "n.white@yale.edu", "interests": "Synaptic Plasticity, Neurodegenerative Diseases, fMRI", "city": "New Haven", "state": "CT", "latitude": 41.3163, "longitude": -72.9223},
    {"name": "Eric Taylor", "university": "Yale", "department": "Chemistry", "email": "e.taylor@yale.edu", "interests": "Chemical Biology, Natural Products, Enzyme Catalysis", "city": "New Haven", "state": "CT", "latitude": 41.3163, "longitude": -72.9223},
    {"name": "Margaret Jackson", "university": "Yale", "department": "Psychology", "email": "m.jackson@yale.edu", "interests": "Developmental Psychology, Child Development, Attachment Theory", "city": "New Haven", "state": "CT", "latitude": 41.3163, "longitude": -72.9223},
    # Columbia - New York, NY
    {"name": "George Lewis", "university": "Columbia", "department": "Computer Science", "email": "g.lewis@columbia.edu", "interests": "Computer Graphics, Virtual Reality, Human-Computer Interaction", "city": "New York", "state": "NY", "latitude": 40.8075, "longitude": -73.9626},
    {"name": "Helen Walker", "university": "Columbia", "department": "Data Science", "email": "h.walker@columbia.edu", "interests": "Causal Inference, Bayesian Methods, Health Data Science", "city": "New York", "state": "NY", "latitude": 40.8075, "longitude": -73.9626},
    {"name": "Charles Hall", "university": "Columbia", "department": "Physics", "email": "c.hall@columbia.edu", "interests": "Quantum Information, Quantum Optics, Atomic Physics", "city": "New York", "state": "NY", "latitude": 40.8075, "longitude": -73.9626},
    # University of Michigan - Ann Arbor, MI
    {"name": "Dorothy Young", "university": "University of Michigan", "department": "Computer Science", "email": "d.young@umich.edu", "interests": "Security, Privacy, Networked Systems", "city": "Ann Arbor", "state": "MI", "latitude": 42.2780, "longitude": -83.7382},
    {"name": "Joseph Allen", "university": "University of Michigan", "department": "Electrical Engineering", "email": "j.allen@umich.edu", "interests": "Power Systems, Renewable Energy, Smart Grid", "city": "Ann Arbor", "state": "MI", "latitude": 42.2780, "longitude": -83.7382},
    {"name": "Carol Scott", "university": "University of Michigan", "department": "Biology", "email": "c.scott@umich.edu", "interests": "Evolutionary Biology, Population Genetics, Ecology", "city": "Ann Arbor", "state": "MI", "latitude": 42.2780, "longitude": -83.7382},
    # Georgia Tech - Atlanta, GA
    {"name": "Kenneth Turner", "university": "Georgia Tech", "department": "Computer Science", "email": "k.turner@gatech.edu", "interests": "Software Engineering, Program Analysis, DevOps", "city": "Atlanta", "state": "GA", "latitude": 33.7756, "longitude": -84.3963},
    {"name": "Sandra Phillips", "university": "Georgia Tech", "department": "Electrical Engineering", "email": "s.phillips@gatech.edu", "interests": "Wireless Communications, 5G Networks, Signal Processing", "city": "Atlanta", "state": "GA", "latitude": 33.7756, "longitude": -84.3963},
    {"name": "Ronald Campbell", "university": "Georgia Tech", "department": "Mathematics", "email": "r.campbell@gatech.edu", "interests": "Discrete Mathematics, Graph Theory, Combinatorics", "city": "Atlanta", "state": "GA", "latitude": 33.7756, "longitude": -84.3963},
    # UT Austin - Austin, TX
    {"name": "Barbara Mitchell", "university": "UT Austin", "department": "Computer Science", "email": "b.mitchell@utexas.edu", "interests": "Programming Languages, Compilers, Type Theory", "city": "Austin", "state": "TX", "latitude": 30.2849, "longitude": -97.7341},
    {"name": "Larry Carter", "university": "UT Austin", "department": "Physics", "email": "l.carter@utexas.edu", "interests": "Nuclear Physics, Plasma Physics, Fusion Energy", "city": "Austin", "state": "TX", "latitude": 30.2849, "longitude": -97.7341},
    {"name": "Betty Roberts", "university": "UT Austin", "department": "Economics", "email": "b.roberts@utexas.edu", "interests": "Environmental Economics, Natural Resources, Climate Policy", "city": "Austin", "state": "TX", "latitude": 30.2849, "longitude": -97.7341},
    # UCLA - Los Angeles, CA
    {"name": "Gary Evans", "university": "UCLA", "department": "Computer Science", "email": "g.evans@ucla.edu", "interests": "Bioinformatics, Computational Biology, Genomic Data", "city": "Los Angeles", "state": "CA", "latitude": 34.0689, "longitude": -118.4452},
    {"name": "Sharon Collins", "university": "UCLA", "department": "Neuroscience", "email": "s.collins@ucla.edu", "interests": "Cognitive Neuroscience, Brain Imaging, Neural Coding", "city": "Los Angeles", "state": "CA", "latitude": 34.0689, "longitude": -118.4452},
    {"name": "Frank Stewart", "university": "UCLA", "department": "Chemistry", "email": "f.stewart@ucla.edu", "interests": "Materials Chemistry, Nanotechnology, Surface Science", "city": "Los Angeles", "state": "CA", "latitude": 34.0689, "longitude": -118.4452},
    {"name": "Deborah Sanchez", "university": "UCLA", "department": "Psychology", "email": "d.sanchez@ucla.edu", "interests": "Clinical Psychology, Anxiety Disorders, Cognitive Behavioral Therapy", "city": "Los Angeles", "state": "CA", "latitude": 34.0689, "longitude": -118.4452},
    # NYU - New York, NY
    {"name": "Raymond Morris", "university": "NYU", "department": "Computer Science", "email": "r.morris@nyu.edu", "interests": "Deep Learning, Computer Vision, Generative Models", "city": "New York", "state": "NY", "latitude": 40.7295, "longitude": -73.9965},
    {"name": "Christine Rogers", "university": "NYU", "department": "Mathematics", "email": "c.rogers@nyu.edu", "interests": "Probability Theory, Stochastic Processes, Financial Mathematics", "city": "New York", "state": "NY", "latitude": 40.7295, "longitude": -73.9965},
    {"name": "Henry Reed", "university": "NYU", "department": "Data Science", "email": "h.reed@nyu.edu", "interests": "Social Network Analysis, Text Mining, Knowledge Graphs", "city": "New York", "state": "NY", "latitude": 40.7295, "longitude": -73.9965},
    # Northwestern - Evanston, IL
    {"name": "Kathleen Cook", "university": "Northwestern", "department": "Computer Science", "email": "k.cook@northwestern.edu", "interests": "Human-Computer Interaction, Accessibility, UX Research", "city": "Evanston", "state": "IL", "latitude": 42.0565, "longitude": -87.6753},
    {"name": "Walter Morgan", "university": "Northwestern", "department": "Biology", "email": "w.morgan@northwestern.edu", "interests": "Cell Biology, Stem Cells, Regenerative Medicine", "city": "Evanston", "state": "IL", "latitude": 42.0565, "longitude": -87.6753},
    {"name": "Donna Bell", "university": "Northwestern", "department": "Neuroscience", "email": "d.bell@northwestern.edu", "interests": "Sleep Research, Circadian Rhythms, Neurological Disorders", "city": "Evanston", "state": "IL", "latitude": 42.0565, "longitude": -87.6753},
    {"name": "Harold Rivera", "university": "Northwestern", "department": "Economics", "email": "h.rivera@northwestern.edu", "interests": "Industrial Organization, Regulation, Competition Policy", "city": "Evanston", "state": "IL", "latitude": 42.0565, "longitude": -87.6753},
]


def seed():
    with app.app_context():
        count = 0
        for data in PROFESSORS:
            if not Professor.query.filter_by(email=data["email"]).first():
                prof = Professor(country="USA", **data)
                db.session.add(prof)
                count += 1
        db.session.commit()
        print(f"Seeded {count} professors ({len(PROFESSORS) - count} already existed)")


if __name__ == "__main__":
    seed()
