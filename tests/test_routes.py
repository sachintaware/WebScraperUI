import unittest
from app import app, db
from models import ScrapedData, User
from datetime import datetime

class TestRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            # Create test user
            user = User(username='test', email='test@test.com')
            user.set_password('test123')
            db.session.add(user)
            # Create test scraped data
            data = ScrapedData(
                url='http://test.com',
                title='Test',
                content='Test content',
                domain='test.com',
                created_at=datetime.utcnow()
            )
            db.session.add(data)
            db.session.commit()

    def test_website_details(self):
        # Login first
        self.client.post('/login', data={
            'username': 'test',
            'password': 'test123'
        })
        # Test website details page
        response = self.client.get('/website/test.com')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test.com', response.data)

    def test_invalid_domain(self):
        # Login first
        self.client.post('/login', data={
            'username': 'test',
            'password': 'test123'
        })
        # Test invalid domain
        response = self.client.get('/website/invalid.com')
        self.assertEqual(response.status_code, 302)  # Should redirect
