import sys
import io

# Set stdout to utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.database.session import SessionLocal
from app.models import Hotel, Restaurant
from app.services.ai.factory import build_providers
from app.services.ai.assistant import AssistantService
from app.core.config import get_settings

db = SessionLocal()
hotel = db.query(Hotel).first()
restaurant = db.query(Restaurant).first()
settings = get_settings()
provider, fallback = build_providers(db, hotel, restaurant.id, settings)
svc = AssistantService(db, hotel, restaurant, provider, fallback)

queries = [
    'What is the price and what would you recommend for starters?',
    'What starters do you have, how much are they, and which is your recommendation?',
    'Tell me the price of paneer tikka and recommend a main course.',
    'What is the cheapest starter and what do you recommend?'
]

for q in queries:
    print('=' * 60)
    print('QUERY:', q)
    session = svc.start_session('en')
    res = svc.chat(session, q, 'en')
    print('PROVIDER:', res.get('provider'))
    print('TOOLS USED:', res.get('tools_used'))
    print('REPLY:\n', res.get('reply'))
