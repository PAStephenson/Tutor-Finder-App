from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CustomUser, Subject, SubjectLevel, Conversation, Message, NewsPost, TokenPurchase, ContactUnlock


class TutorSearchTests(TestCase):
    def setUp(self):
        self.maths = Subject.objects.create(name='Maths')
        self.english = Subject.objects.create(name='English')
        self.gcse = SubjectLevel.objects.create(name='GCSE')

        self.approved_tutor = CustomUser.objects.create_user(
            email='approved@example.com', password='testpass123',
            first_name='Approved', last_name='Tutor', role=CustomUser.ROLE_TUTOR,
            cost=30, documents_approved=True, references_approved=True,
            id_check_completed=True,
        )
        self.approved_tutor.subjects.add(self.maths)
        self.approved_tutor.subject_levels.add(self.gcse)

        self.pending_tutor = CustomUser.objects.create_user(
            email='pending@example.com', password='testpass123',
            first_name='Pending', last_name='Tutor', role=CustomUser.ROLE_TUTOR,
            cost=20, documents_approved=False, references_approved=True,
            id_check_completed=True,
        )
        self.pending_tutor.subjects.add(self.english)
        self.pending_tutor.subject_levels.add(self.gcse)

        self.parent = CustomUser.objects.create_user(
            email='parent@example.com', password='testpass123',
            first_name='Jane', last_name='Parent', role=CustomUser.ROLE_PARENT,
        )

    def test_search_requires_login(self):
        response = self.client.get(reverse('tutor_search'))
        self.assertEqual(response.status_code, 302)

    def test_search_page_only_lists_fully_approved_tutors(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_search'))
        self.assertEqual(response.status_code, 200)
        tutors = list(response.context['page_obj'])
        self.assertIn(self.approved_tutor, tutors)
        self.assertNotIn(self.pending_tutor, tutors)

    def test_search_excludes_parent_accounts(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_search'))
        tutors = list(response.context['page_obj'])
        self.assertNotIn(self.parent, tutors)

    def test_search_filters_by_subject(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_search'), {'subject': self.english.id})
        tutors = list(response.context['page_obj'])
        self.assertNotIn(self.approved_tutor, tutors)

    def test_search_filters_by_max_price(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_search'), {'max_price': '10'})
        tutors = list(response.context['page_obj'])
        self.assertNotIn(self.approved_tutor, tutors)

    def test_search_handles_invalid_max_price_gracefully(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_search'), {'max_price': 'not-a-number'})
        self.assertEqual(response.status_code, 200)

    def test_search_excludes_unavailable_tutors(self):
        self.approved_tutor.availability = CustomUser.AVAILABILITY_NOT_AVAILABLE
        self.approved_tutor.save()
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_search'))
        tutors = list(response.context['page_obj'])
        self.assertNotIn(self.approved_tutor, tutors)

    def test_search_includes_available_tutors_by_default(self):
        self.assertEqual(self.approved_tutor.availability, CustomUser.AVAILABILITY_AVAILABLE)
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_search'))
        tutors = list(response.context['page_obj'])
        self.assertIn(self.approved_tutor, tutors)

    def test_tutor_detail_still_accessible_when_unavailable(self):
        self.approved_tutor.availability = CustomUser.AVAILABILITY_NOT_AVAILABLE
        self.approved_tutor.save()
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_detail', args=[self.approved_tutor.pk]))
        self.assertEqual(response.status_code, 200)

    def test_tutor_detail_requires_login(self):
        response = self.client.get(reverse('tutor_detail', args=[self.approved_tutor.pk]))
        self.assertEqual(response.status_code, 302)

    def test_tutor_detail_visible_for_approved_tutor(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_detail', args=[self.approved_tutor.pk]))
        self.assertEqual(response.status_code, 200)

    def test_tutor_detail_404s_for_unapproved_tutor(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_detail', args=[self.pending_tutor.pk]))
        self.assertEqual(response.status_code, 404)


class ConversationTests(TestCase):
    def setUp(self):
        self.maths = Subject.objects.create(name='Maths')
        self.gcse = SubjectLevel.objects.create(name='GCSE')
        self.tutor = CustomUser.objects.create_user(
            email='tutor@example.com', password='testpass123',
            first_name='Approved', last_name='Tutor', role=CustomUser.ROLE_TUTOR,
            cost=30, documents_approved=True, references_approved=True,
            id_check_completed=True,
        )
        self.tutor.subjects.add(self.maths)
        self.tutor.subject_levels.add(self.gcse)

        self.other_tutor = CustomUser.objects.create_user(
            email='other_tutor@example.com', password='testpass123',
            first_name='Other', last_name='Tutor', role=CustomUser.ROLE_TUTOR,
            cost=25, documents_approved=True, references_approved=True,
            id_check_completed=True,
        )

        self.parent = CustomUser.objects.create_user(
            email='parent@example.com', password='testpass123',
            first_name='Jane', last_name='Parent', role=CustomUser.ROLE_PARENT,
        )
        self.other_parent = CustomUser.objects.create_user(
            email='other_parent@example.com', password='testpass123',
            first_name='Bob', last_name='Parent', role=CustomUser.ROLE_PARENT,
        )

    def test_starting_a_conversation_creates_it_with_first_message_and_redirects(self):
        self.client.force_login(self.parent)
        response = self.client.post(reverse('tutor_detail', args=[self.tutor.pk]), {
            'body': 'Looking for GCSE Maths tutoring for my son.',
        })
        self.assertEqual(Conversation.objects.count(), 1)
        conversation = Conversation.objects.first()
        self.assertEqual(conversation.tutor, self.tutor)
        self.assertEqual(conversation.parent, self.parent)
        self.assertRedirects(response, reverse('conversation_detail', args=[conversation.pk]))

        self.assertEqual(conversation.messages.count(), 1)
        first_message = conversation.messages.first()
        self.assertEqual(first_message.sender, Message.SENDER_PARENT)
        self.assertEqual(first_message.body, 'Looking for GCSE Maths tutoring for my son.')

    def test_messaging_the_same_tutor_twice_reuses_the_conversation(self):
        self.client.force_login(self.parent)
        self.client.post(reverse('tutor_detail', args=[self.tutor.pk]), {'body': 'First message'})
        self.client.post(reverse('tutor_detail', args=[self.tutor.pk]), {'body': 'Second message'})

        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Conversation.objects.first().messages.count(), 2)

    def test_invalid_start_form_creates_nothing(self):
        self.client.force_login(self.parent)
        response = self.client.post(reverse('tutor_detail', args=[self.tutor.pk]), {'body': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_cannot_start_conversation_about_unapproved_tutor(self):
        pending_tutor = CustomUser.objects.create_user(
            email='pending2@example.com', password='testpass123', role=CustomUser.ROLE_TUTOR,
            documents_approved=False, references_approved=True,
            id_check_completed=True,
        )
        self.client.force_login(self.parent)
        response = self.client.post(reverse('tutor_detail', args=[pending_tutor.pk]), {'body': 'Hello'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_parent_can_view_and_reply_to_their_own_conversation(self):
        conversation = Conversation.objects.create(tutor=self.tutor, parent=self.parent)
        Message.objects.create(conversation=conversation, sender=Message.SENDER_PARENT, body='Hi there')

        self.client.force_login(self.parent)
        response = self.client.get(reverse('conversation_detail', args=[conversation.pk]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('conversation_detail', args=[conversation.pk]), {
            'body': 'Following up on my earlier message.',
        })
        self.assertRedirects(response, reverse('conversation_detail', args=[conversation.pk]))
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(conversation.messages.last().sender, Message.SENDER_PARENT)

    def test_tutor_can_view_and_reply_to_their_own_conversation(self):
        conversation = Conversation.objects.create(tutor=self.tutor, parent=self.parent)
        Message.objects.create(conversation=conversation, sender=Message.SENDER_PARENT, body='Hi there')

        self.client.force_login(self.tutor)
        response = self.client.post(reverse('conversation_detail', args=[conversation.pk]), {
            'body': 'Happy to help!',
        })
        self.assertRedirects(response, reverse('conversation_detail', args=[conversation.pk]))
        self.assertEqual(conversation.messages.last().sender, Message.SENDER_TUTOR)

    def test_conversation_detail_requires_login(self):
        conversation = Conversation.objects.create(tutor=self.tutor, parent=self.parent)
        response = self.client.get(reverse('conversation_detail', args=[conversation.pk]))
        self.assertEqual(response.status_code, 302)

    def test_conversation_detail_404s_for_non_participant(self):
        conversation = Conversation.objects.create(tutor=self.tutor, parent=self.parent)
        self.client.force_login(self.other_parent)
        response = self.client.get(reverse('conversation_detail', args=[conversation.pk]))
        self.assertEqual(response.status_code, 404)

    def test_message_inbox_requires_login(self):
        response = self.client.get(reverse('message_inbox'))
        self.assertEqual(response.status_code, 302)

    def test_message_inbox_shows_conversations_for_either_side(self):
        my_conversation_as_tutor = Conversation.objects.create(tutor=self.tutor, parent=self.parent)
        Conversation.objects.create(tutor=self.other_tutor, parent=self.other_parent)

        self.client.force_login(self.tutor)
        response = self.client.get(reverse('message_inbox'))
        self.assertEqual(list(response.context['conversations']), [my_conversation_as_tutor])

        my_conversation_as_parent = Conversation.objects.create(tutor=self.other_tutor, parent=self.parent)
        self.client.force_login(self.parent)
        response = self.client.get(reverse('message_inbox'))
        conversations = set(response.context['conversations'])
        self.assertEqual(conversations, {my_conversation_as_tutor, my_conversation_as_parent})


class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.tutor = CustomUser.objects.create_user(
            email='tutor@example.com', password='testpass123', role=CustomUser.ROLE_TUTOR,
        )
        self.parent = CustomUser.objects.create_user(
            email='parent@example.com', password='testpass123', role=CustomUser.ROLE_PARENT,
        )

    def test_parent_signup_creates_parent_role_and_logs_in(self):
        response = self.client.post(reverse('parent_signup'), {
            'first_name': 'New', 'last_name': 'Parent', 'email': 'newparent@example.com',
            'password1': 'a-strong-password-1', 'password2': 'a-strong-password-1',
            'terms_agreed': 'on',
        })
        self.assertRedirects(response, reverse('tutor_search'))
        new_user = CustomUser.objects.get(email='newparent@example.com')
        self.assertEqual(new_user.role, CustomUser.ROLE_PARENT)
        self.assertTrue(new_user.is_parent)

    def test_parent_signup_requires_terms_agreement(self):
        response = self.client.post(reverse('parent_signup'), {
            'first_name': 'New', 'last_name': 'Parent', 'email': 'newparent2@example.com',
            'password1': 'a-strong-password-1', 'password2': 'a-strong-password-1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='newparent2@example.com').exists())

    def test_tutor_signup_still_creates_tutor_role(self):
        response = self.client.post(reverse('signup'), {
            'first_name': 'New', 'last_name': 'Tutor', 'email': 'newtutor@example.com',
            'password1': 'a-strong-password-1', 'password2': 'a-strong-password-1',
            'terms_agreed': 'on',
        })
        self.assertRedirects(response, reverse('profile'))
        new_user = CustomUser.objects.get(email='newtutor@example.com')
        self.assertEqual(new_user.role, CustomUser.ROLE_TUTOR)
        self.assertTrue(new_user.is_tutor)

    def test_login_redirects_parent_to_tutor_search(self):
        response = self.client.post(reverse('login'), {
            'username': 'parent@example.com', 'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('tutor_search'))

    def test_login_redirects_tutor_to_profile(self):
        response = self.client.post(reverse('login'), {
            'username': 'tutor@example.com', 'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('profile'))

    def test_parent_cannot_view_tutor_profile_page(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, reverse('tutor_search'))

    def test_parent_cannot_view_edit_profile_page(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('edit_profile'))
        self.assertRedirects(response, reverse('tutor_search'))


class ParentSignupFlagTests(TestCase):
    def test_parent_signup_visible_by_default(self):
        response = self.client.get(reverse('home'))
        self.assertTrue(response.context['parent_signup_enabled'])
        response = self.client.get(reverse('parent_signup'))
        self.assertEqual(response.status_code, 200)

    @override_settings(HIDE_PARENT_SIGNUP=True)
    def test_parent_signup_page_redirects_home_when_hidden(self):
        response = self.client.get(reverse('parent_signup'))
        self.assertRedirects(response, reverse('home'))

    @override_settings(HIDE_PARENT_SIGNUP=True)
    def test_parent_signup_post_also_blocked_when_hidden(self):
        response = self.client.post(reverse('parent_signup'), {
            'first_name': 'New', 'last_name': 'Parent', 'email': 'blocked@example.com',
            'password1': 'a-strong-password-1', 'password2': 'a-strong-password-1',
            'terms_agreed': 'on',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(CustomUser.objects.filter(email='blocked@example.com').exists())

    @override_settings(HIDE_PARENT_SIGNUP=True)
    def test_context_flag_false_when_hidden(self):
        response = self.client.get(reverse('home'))
        self.assertFalse(response.context['parent_signup_enabled'])


class AdminUserManagementTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(email='admin@example.com', password='adminpass123')
        self.client.force_login(self.admin)

    def test_admin_can_create_a_parent_account(self):
        response = self.client.post('/admin/accounts/customuser/add/', {
            'email': 'newparent@example.com',
            'password1': 'a-strong-password-1',
            'password2': 'a-strong-password-1',
            'role': CustomUser.ROLE_PARENT,
        })
        self.assertEqual(response.status_code, 302)
        new_user = CustomUser.objects.get(email='newparent@example.com')
        self.assertTrue(new_user.is_parent)

    def test_admin_can_create_a_tutor_account(self):
        response = self.client.post('/admin/accounts/customuser/add/', {
            'email': 'newtutor@example.com',
            'password1': 'a-strong-password-1',
            'password2': 'a-strong-password-1',
            'role': CustomUser.ROLE_TUTOR,
        })
        self.assertEqual(response.status_code, 302)
        new_user = CustomUser.objects.get(email='newtutor@example.com')
        self.assertTrue(new_user.is_tutor)

    def test_admin_change_form_round_trip(self):
        tutor = CustomUser.objects.create_user(
            email='t@example.com', password='pass12345', role=CustomUser.ROLE_TUTOR,
        )
        response = self.client.get(f'/admin/accounts/customuser/{tutor.pk}/change/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f'/admin/accounts/customuser/{tutor.pk}/change/', {
            'email': 'edited@example.com',
            'role': CustomUser.ROLE_TUTOR,
            'first_name': 'Edited',
            'last_name': 'Name',
            'bio': '',
            'phone_number': '',
            'token_balance': '0',
            'availability': CustomUser.AVAILABILITY_AVAILABLE,
            'is_active': 'on',
            'date_joined_0': tutor.date_joined.strftime('%Y-%m-%d'),
            'date_joined_1': tutor.date_joined.strftime('%H:%M:%S'),
            'subjects': [],
            'subject_levels': [],
            'groups': [],
            'user_permissions': [],
        })
        self.assertEqual(response.status_code, 302)
        tutor.refresh_from_db()
        self.assertEqual(tutor.first_name, 'Edited')
        self.assertEqual(tutor.email, 'edited@example.com')


class NewsTests(TestCase):
    def setUp(self):
        self.oldest = NewsPost.objects.create(title='Oldest', body='First post', published_at='2026-01-01T00:00:00Z')
        self.middle = NewsPost.objects.create(title='Middle', body='Second post', published_at='2026-02-01T00:00:00Z')
        self.newest = NewsPost.objects.create(title='Newest', body='Third post', published_at='2026-03-01T00:00:00Z')

    def test_news_list_is_public(self):
        response = self.client.get(reverse('news_list'))
        self.assertEqual(response.status_code, 200)

    def test_news_list_sorted_newest_first(self):
        response = self.client.get(reverse('news_list'))
        posts = list(response.context['news_posts'])
        self.assertEqual(posts, [self.newest, self.middle, self.oldest])

    def test_home_page_shows_latest_three_news_posts(self):
        NewsPost.objects.create(title='Even Newer', body='Fourth post', published_at='2026-04-01T00:00:00Z')
        response = self.client.get(reverse('home'))
        latest_news = list(response.context['latest_news'])
        self.assertEqual(len(latest_news), 3)
        self.assertEqual(latest_news[0].title, 'Even Newer')

    def test_home_page_with_no_news(self):
        NewsPost.objects.all().delete()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['latest_news']), [])


class BuyTokensTests(TestCase):
    def setUp(self):
        self.parent = CustomUser.objects.create_user(
            email='parent@example.com', password='testpass123', role=CustomUser.ROLE_PARENT,
        )
        self.tutor = CustomUser.objects.create_user(
            email='tutor@example.com', password='testpass123', role=CustomUser.ROLE_TUTOR,
        )

    def test_buy_tokens_requires_login(self):
        response = self.client.get(reverse('buy_tokens'))
        self.assertEqual(response.status_code, 302)

    def test_tutor_cannot_access_buy_tokens(self):
        self.client.force_login(self.tutor)
        response = self.client.get(reverse('buy_tokens'))
        self.assertRedirects(response, reverse('home'))

    def test_buy_tokens_page_shows_balance_and_price(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('buy_tokens'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['token_price_pounds'], 5.0)

    def test_purchase_blocked_without_stripe_keys_configured(self):
        self.client.force_login(self.parent)
        response = self.client.post(reverse('buy_tokens'), {'quantity': '2'})
        self.assertRedirects(response, reverse('buy_tokens'))
        self.assertEqual(TokenPurchase.objects.count(), 0)

    @override_settings(STRIPE_SECRET_KEY='sk_test_fake')
    @patch('accounts.views.stripe.checkout.Session.create')
    def test_purchase_creates_pending_record_and_redirects_to_stripe(self, mock_create):
        mock_create.return_value = SimpleNamespace(id='cs_test_123', url='https://checkout.stripe.com/pay/cs_test_123')

        self.client.force_login(self.parent)
        response = self.client.post(reverse('buy_tokens'), {'quantity': '3'})

        self.assertRedirects(response, 'https://checkout.stripe.com/pay/cs_test_123', fetch_redirect_response=False)
        purchase = TokenPurchase.objects.get(stripe_checkout_session_id='cs_test_123')
        self.assertEqual(purchase.parent, self.parent)
        self.assertEqual(purchase.tokens, 3)
        self.assertEqual(purchase.amount_pence, 1500)
        self.assertEqual(purchase.status, TokenPurchase.STATUS_PENDING)

    @override_settings(STRIPE_SECRET_KEY='sk_test_fake')
    def test_invalid_quantity_rejected(self):
        self.client.force_login(self.parent)
        response = self.client.post(reverse('buy_tokens'), {'quantity': '0'})
        self.assertRedirects(response, reverse('buy_tokens'))
        self.assertEqual(TokenPurchase.objects.count(), 0)


class StripeWebhookTests(TestCase):
    def setUp(self):
        self.parent = CustomUser.objects.create_user(
            email='parent@example.com', password='testpass123', role=CustomUser.ROLE_PARENT,
        )
        self.purchase = TokenPurchase.objects.create(
            parent=self.parent, tokens=5, amount_pence=2500,
            stripe_checkout_session_id='cs_test_abc',
        )

    def _completed_event(self, session_id='cs_test_abc'):
        return {'type': 'checkout.session.completed', 'data': {'object': {'id': session_id}}}

    @patch('accounts.views.stripe.Webhook.construct_event')
    def test_webhook_credits_tokens_on_completion(self, mock_construct):
        mock_construct.return_value = self._completed_event()
        response = self.client.post(
            reverse('stripe_webhook'), data=b'{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=fake',
        )
        self.assertEqual(response.status_code, 200)

        self.purchase.refresh_from_db()
        self.parent.refresh_from_db()
        self.assertEqual(self.purchase.status, TokenPurchase.STATUS_COMPLETED)
        self.assertIsNotNone(self.purchase.completed_at)
        self.assertEqual(self.parent.token_balance, 5)

    @patch('accounts.views.stripe.Webhook.construct_event')
    def test_webhook_is_idempotent_on_redelivery(self, mock_construct):
        mock_construct.return_value = self._completed_event()
        for _ in range(2):
            self.client.post(
                reverse('stripe_webhook'), data=b'{}', content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=1,v1=fake',
            )
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.token_balance, 5)

    @patch('accounts.views.stripe.Webhook.construct_event')
    def test_webhook_ignores_unknown_session(self, mock_construct):
        mock_construct.return_value = self._completed_event(session_id='cs_unknown')
        response = self.client.post(
            reverse('stripe_webhook'), data=b'{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=fake',
        )
        self.assertEqual(response.status_code, 200)
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.token_balance, 0)

    @patch('accounts.views.stripe.Webhook.construct_event')
    def test_webhook_rejects_bad_signature(self, mock_construct):
        import stripe
        mock_construct.side_effect = stripe.SignatureVerificationError('bad sig', 'sig_header')
        response = self.client.post(
            reverse('stripe_webhook'), data=b'{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='bad',
        )
        self.assertEqual(response.status_code, 400)

    def test_webhook_rejects_get(self):
        response = self.client.get(reverse('stripe_webhook'))
        self.assertEqual(response.status_code, 405)


class UnlockTutorContactTests(TestCase):
    def setUp(self):
        self.maths = Subject.objects.create(name='Maths')
        self.gcse = SubjectLevel.objects.create(name='GCSE')
        self.tutor = CustomUser.objects.create_user(
            email='tutor@example.com', password='testpass123', role=CustomUser.ROLE_TUTOR,
            first_name='Tina', cost=30, documents_approved=True, references_approved=True,
            id_check_completed=True, phone_number='07700900000',
        )
        self.tutor.subjects.add(self.maths)
        self.tutor.subject_levels.add(self.gcse)

        self.parent = CustomUser.objects.create_user(
            email='parent@example.com', password='testpass123', role=CustomUser.ROLE_PARENT,
            token_balance=2,
        )

    def test_unlock_requires_login(self):
        response = self.client.post(reverse('unlock_tutor_contact', args=[self.tutor.pk]))
        self.assertEqual(response.status_code, 302)

    def test_unlock_requires_post(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('unlock_tutor_contact', args=[self.tutor.pk]))
        self.assertEqual(response.status_code, 405)

    def test_successful_unlock_spends_one_token(self):
        self.client.force_login(self.parent)
        response = self.client.post(reverse('unlock_tutor_contact', args=[self.tutor.pk]))
        self.assertRedirects(response, reverse('tutor_detail', args=[self.tutor.pk]))

        self.parent.refresh_from_db()
        self.assertEqual(self.parent.token_balance, 1)
        self.assertTrue(ContactUnlock.objects.filter(parent=self.parent, tutor=self.tutor).exists())

    def test_unlock_with_no_tokens_is_blocked(self):
        self.parent.token_balance = 0
        self.parent.save()
        self.client.force_login(self.parent)
        response = self.client.post(reverse('unlock_tutor_contact', args=[self.tutor.pk]))
        self.assertRedirects(response, reverse('buy_tokens'))

        self.parent.refresh_from_db()
        self.assertEqual(self.parent.token_balance, 0)
        self.assertFalse(ContactUnlock.objects.filter(parent=self.parent, tutor=self.tutor).exists())

    def test_already_unlocked_does_not_charge_again(self):
        ContactUnlock.objects.create(parent=self.parent, tutor=self.tutor)
        self.client.force_login(self.parent)
        response = self.client.post(reverse('unlock_tutor_contact', args=[self.tutor.pk]))
        self.assertRedirects(response, reverse('tutor_detail', args=[self.tutor.pk]))

        self.parent.refresh_from_db()
        self.assertEqual(self.parent.token_balance, 2)
        self.assertEqual(ContactUnlock.objects.filter(parent=self.parent, tutor=self.tutor).count(), 1)

    def test_tutor_cannot_spend_tokens(self):
        other_tutor = CustomUser.objects.create_user(
            email='other@example.com', password='testpass123', role=CustomUser.ROLE_TUTOR,
        )
        self.client.force_login(other_tutor)
        response = self.client.post(reverse('unlock_tutor_contact', args=[self.tutor.pk]))
        self.assertRedirects(response, reverse('tutor_detail', args=[self.tutor.pk]))
        self.assertFalse(ContactUnlock.objects.filter(tutor=self.tutor).exists())

    def test_unapproved_tutor_404s(self):
        pending_tutor = CustomUser.objects.create_user(
            email='pending@example.com', password='testpass123', role=CustomUser.ROLE_TUTOR,
            documents_approved=False, references_approved=True, id_check_completed=True,
        )
        self.client.force_login(self.parent)
        response = self.client.post(reverse('unlock_tutor_contact', args=[pending_tutor.pk]))
        self.assertEqual(response.status_code, 404)

    def test_tutor_detail_hides_contact_until_unlocked(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_detail', args=[self.tutor.pk]))
        self.assertFalse(response.context['is_unlocked'])
        self.assertNotContains(response, '07700900000')

    def test_tutor_detail_shows_contact_once_unlocked(self):
        ContactUnlock.objects.create(parent=self.parent, tutor=self.tutor)
        self.client.force_login(self.parent)
        response = self.client.get(reverse('tutor_detail', args=[self.tutor.pk]))
        self.assertTrue(response.context['is_unlocked'])
        self.assertContains(response, '07700900000')
        self.assertContains(response, 'tutor@example.com')
