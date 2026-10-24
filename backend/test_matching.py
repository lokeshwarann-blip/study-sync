from app.database import SessionLocal
from app import models, matching

db = SessionLocal()
alex = db.query(models.User).filter_by(email="alex@univ.edu").first()
print(f"Loaded User: {alex.name} ({alex.email})")

user_ratings = {ut.topic_id: ut.rating for ut in alex.topics}
user_slots = {(a.day, a.hour) for a in alex.availability}
topic_dict = {t.id: t.name for t in db.query(models.Topic).all()}

groups = db.query(models.Group).all()
print(f"Total Groups in SQLite: {len(groups)}")

for g in groups:
    members_ratings = {}
    members_slots = []
    top_helper_name = ""
    top_helper_score = 0
    for m in g.members:
        u = m.user
        m_r = {ut.topic_id: ut.rating for ut in u.topics}
        members_ratings[u.id] = m_r
        members_slots.append({(a.day, a.hour) for a in u.availability})
        for t_id, my_r in user_ratings.items():
            if my_r <= 2 and m_r.get(t_id, 0) > top_helper_score:
                top_helper_score = m_r.get(t_id, 0)
                top_helper_name = u.name

    best = matching.group_strength(members_ratings)
    s_skill, h_in, h_out = matching.skill_score(user_ratings, best)
    s_sched, overlap = matching.schedule_score(user_slots, members_slots)
    final = matching.final_score(s_skill, s_sched)
    why, weak_b, strong_b = matching.generate_why_matched(user_ratings, best, topic_dict, overlap, top_helper_name)

    print(f"--> Group: {g.name:<20} | Score: {final}% | Skill: {s_skill:.1f} | Sched: {s_sched:.1f} | Overlap: {overlap}h")
    print(f"    Why: {why}")

db.close()
