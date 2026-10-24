import random
from app.database import SessionLocal, engine, Base
from app import models, auth

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def seed():
    # Use deterministic seed for reproducible hackathon demo
    random.seed(42)
    db = SessionLocal()

    # Clear existing data
    db.query(models.GroupMember).delete()
    db.query(models.Group).delete()
    db.query(models.UserTopic).delete()
    db.query(models.Availability).delete()
    db.query(models.Topic).delete()
    db.query(models.User).delete()
    db.commit()

    print("Seeding topics...")
    topics_list = [
        ("Dynamic Programming", "Algorithms"),
        ("Graph Algorithms", "Algorithms"),
        ("NP-Completeness", "Algorithms"),
        ("Divide & Conquer", "Algorithms"),
        ("Greedy Algorithms", "Algorithms"),
        ("Operating Systems & Concurrency", "Systems"),
        ("Computer Networks", "Systems"),
        ("Machine Learning Foundations", "AI"),
        ("Deep Learning & PyTorch", "AI"),
        ("Database Systems & SQL", "Systems"),
    ]

    topic_objs = []
    for name, cat in topics_list:
        t = models.Topic(name=name, category=cat)
        db.add(t)
        topic_objs.append(t)
    db.commit()

    t_map = {t.name: t.id for t in topic_objs}

    print("Seeding primary demo user (Alex Chen)...")
    # Alex Chen: CS Senior
    # Weak: Dynamic Programming (2/5), NP-Completeness (1/5)
    # Strong: Graph Algorithms (5/5), Operating Systems & Concurrency (5/5)
    # Slots: Tue & Thu afternoons (13:00 to 18:00) -> slots 13, 14, 15, 16, 17, 18
    alex = models.User(
        name="Alex Chen",
        email="alex@univ.edu",
        hashed_password=auth.hash_password("password123"),
        major="Computer Science, Senior",
        avatar="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&q=80"
    )
    db.add(alex)
    db.commit()
    db.refresh(alex)

    alex_ratings = [
        (t_map["Dynamic Programming"], 2),
        (t_map["NP-Completeness"], 1),
        (t_map["Graph Algorithms"], 5),
        (t_map["Operating Systems & Concurrency"], 5),
        (t_map["Divide & Conquer"], 3),
        (t_map["Greedy Algorithms"], 4),
    ]
    for tid, r in alex_ratings:
        db.add(models.UserTopic(user_id=alex.id, topic_id=tid, rating=r))

    # Alex free hours: 12 total slots across Tue, Thu, and Sat
    alex_slots = [
        ("Tue", 13), ("Tue", 14), ("Tue", 15), ("Tue", 16), ("Tue", 17), ("Tue", 18),
        ("Thu", 13), ("Thu", 14), ("Thu", 15), ("Thu", 16), ("Thu", 17), ("Thu", 18),
        ("Sat", 14), ("Sat", 15),
    ]
    for day, hr in alex_slots:
        db.add(models.Availability(user_id=alex.id, day=day, hour=hr))
    db.commit()

    print("Seeding demo groups with designed archetypes...")

    # Group 1: AlgoRhythms (Perfect reciprocal complement + high overlap >= 8 hours)
    # Members: Marcus Vance & Chloe Kim
    # Marcus: DP 5/5, NP 5/5, Graph 2/5 -> perfectly covers Alex's gaps!
    # Overlap with Alex: Tue 13-17 (5 hrs), Thu 13-17 (5 hrs) = 10 hours overlap!
    g1 = models.Group(
        name="AlgoRhythms",
        course="CS 4820: Algorithms",
        image="https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=1200&q=80",
        max_members=5
    )
    db.add(g1)
    db.commit()

    marcus = models.User(
        name="Marcus Vance",
        email="marcus@univ.edu",
        hashed_password=auth.hash_password("password123"),
        major="Computer Science, Junior",
        avatar="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80"
    )
    chloe = models.User(
        name="Chloe Kim",
        email="chloe@univ.edu",
        hashed_password=auth.hash_password("password123"),
        major="Software Engineering, Junior",
        avatar="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&q=80"
    )
    db.add_all([marcus, chloe])
    db.commit()

    db.add_all([
        models.GroupMember(group_id=g1.id, user_id=marcus.id, role="leader"),
        models.GroupMember(group_id=g1.id, user_id=chloe.id, role="member"),
    ])

    marcus_ratings = [
        (t_map["Dynamic Programming"], 5),
        (t_map["NP-Completeness"], 5),
        (t_map["Graph Algorithms"], 2),
        (t_map["Operating Systems & Concurrency"], 2),
    ]
    for tid, r in marcus_ratings:
        db.add(models.UserTopic(user_id=marcus.id, topic_id=tid, rating=r))

    chloe_ratings = [
        (t_map["Dynamic Programming"], 4),
        (t_map["Divide & Conquer"], 5),
        (t_map["Graph Algorithms"], 1),
    ]
    for tid, r in chloe_ratings:
        db.add(models.UserTopic(user_id=chloe.id, topic_id=tid, rating=r))

    # Slots for Marcus & Chloe: high overlap on Tue & Thu
    for hr in [13, 14, 15, 16, 17]:
        db.add(models.Availability(user_id=marcus.id, day="Tue", hour=hr))
        db.add(models.Availability(user_id=marcus.id, day="Thu", hour=hr))
        db.add(models.Availability(user_id=chloe.id, day="Tue", hour=hr))
        db.add(models.Availability(user_id=chloe.id, day="Thu", hour=hr))
    db.commit()

    # Group 2: Graph Titans (Strong math/divide & conquer, moderate overlap)
    g2 = models.Group(
        name="Graph Titans",
        course="CS 4820: Algorithms",
        image="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200&q=80",
        max_members=5
    )
    db.add(g2)
    db.commit()

    elena = models.User(
        name="Elena Rostova",
        email="elena@univ.edu",
        hashed_password=auth.hash_password("password123"),
        major="Data Science, Senior",
        avatar="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&q=80"
    )
    db.add(elena)
    db.commit()
    db.add(models.GroupMember(group_id=g2.id, user_id=elena.id, role="leader"))
    for tid, r in [(t_map["Divide & Conquer"], 5), (t_map["NP-Completeness"], 4), (t_map["Dynamic Programming"], 3)]:
        db.add(models.UserTopic(user_id=elena.id, topic_id=tid, rating=r))
    for hr in [14, 15, 16]:
        db.add(models.Availability(user_id=elena.id, day="Tue", hour=hr))
        db.add(models.Availability(user_id=elena.id, day="Sat", hour=hr))
    db.commit()

    # Group 3: Neural Nomads (Machine Learning Focus)
    g3 = models.Group(
        name="Neural Nomads",
        course="CS 4780: Machine Learning",
        image="https://images.unsplash.com/photo-1531482615713-2afd69097998?w=1200&q=80",
        max_members=4
    )
    db.add(g3)
    db.commit()
    devon = models.User(
        name="Devon Zhao",
        email="devon@univ.edu",
        hashed_password=auth.hash_password("password123"),
        major="Software Engineering, Sophomore",
        avatar="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&q=80"
    )
    db.add(devon)
    db.commit()
    db.add(models.GroupMember(group_id=g3.id, user_id=devon.id, role="leader"))
    for tid, r in [(t_map["Machine Learning Foundations"], 5), (t_map["Deep Learning & PyTorch"], 5), (t_map["Dynamic Programming"], 1)]:
        db.add(models.UserTopic(user_id=devon.id, topic_id=tid, rating=r))
    for hr in [13, 14, 15]:
        db.add(models.Availability(user_id=devon.id, day="Thu", hour=hr))
    db.commit()

    # Group 4: Kernel Panic Squad (Operating Systems & Low-level systems)
    g4 = models.Group(
        name="Kernel Panic Squad",
        course="CS 4410: Operating Systems",
        image="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200&q=80",
        max_members=4
    )
    db.add(g4)
    db.commit()
    sarah = models.User(
        name="Sarah Jenkins",
        email="sarah@univ.edu",
        hashed_password=auth.hash_password("password123"),
        major="Computer Engineering, Senior",
        avatar="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&q=80"
    )
    db.add(sarah)
    db.commit()
    db.add(models.GroupMember(group_id=g4.id, user_id=sarah.id, role="leader"))
    for tid, r in [(t_map["Operating Systems & Concurrency"], 4), (t_map["Computer Networks"], 5)]:
        db.add(models.UserTopic(user_id=sarah.id, topic_id=tid, rating=r))
    for hr in [16, 17, 18]:
        db.add(models.Availability(user_id=sarah.id, day="Tue", hour=hr))
    db.commit()

    # Additional Groups: Byte Builders & Data Dynamos
    g5 = models.Group(
        name="Byte Builders",
        course="CS 3110: Functional Programming",
        image="https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=1200&q=80",
        max_members=5
    )
    g6 = models.Group(
        name="Data Dynamos",
        course="INFO 3300: Data Visualization",
        image="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&q=80",
        max_members=5
    )
    db.add_all([g5, g6])
    db.commit()

    print("Seeding 40 background mock students to simulate an active university ecosystem...")
    first_names = ["Liam", "Noah", "Oliver", "James", "Emma", "Olivia", "Sophia", "Isabella", "Lucas", "Henry", "Mia", "Harper", "Ethan", "Aiden", "Zoe", "Leo", "Maya", "Aria", "Jack", "Kai"]
    last_names = ["Smith", "Patel", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    for i in range(1, 41):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        user = models.User(
            name=f"{fn} {ln}",
            email=f"{fn.lower()}.{ln.lower()}{i}@univ.edu",
            hashed_password=auth.hash_password("password123"),
            major="Computer Science",
            avatar=f"https://images.unsplash.com/photo-{1500000000000 + i}?w=400&q=80"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Assign 4 random topics
        assigned_topics = random.sample(topic_objs, 4)
        for t in assigned_topics:
            rating = random.randint(1, 5)
            db.add(models.UserTopic(user_id=user.id, topic_id=t.id, rating=rating))

        # Assign 5-8 unique random slots
        assigned_slots = set()
        while len(assigned_slots) < random.randint(5, 8):
            d = random.choice(days)
            h = random.randint(9, 21)
            assigned_slots.add((d, h))

        for d, h in assigned_slots:
            db.add(models.Availability(user_id=user.id, day=d, hour=h))

        # Randomly assign to Byte Builders or Data Dynamos if not full
        if i % 3 == 0:
            target_g = g5 if i % 2 == 0 else g6
            current_c = db.query(models.GroupMember).filter_by(group_id=target_g.id).count()
            if current_c < target_g.max_members:
                db.add(models.GroupMember(group_id=target_g.id, user_id=user.id, role="member"))

    db.commit()
    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
