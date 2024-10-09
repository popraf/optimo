from django.test import TestCase, Client
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from app.models import Book


class BookListCacheTest(TestCase):
    def setUp(self):
        cache.clear()  # clear the cache before each test
        self.client = Client()
        self.book1 = Book.objects.create(
            title='Book 1',
            author='Author 1',
            isbn='1111',
            count_in_library=5,
            library='Main Library'
        )
        self.book2 = Book.objects.create(
            title='Book 2',
            author='Author 2',
            isbn='2222',
            count_in_library=3,
            library='Main Library'
        )
        self.books_url = reverse('book-list')

    def test_books_list_cached(self):
        """
        Test that the books list is cached and invalidated appropriately.
        """
        cached_books = cache.get('books_list')  # Ensure cache is empty
        self.assertIsNone(cached_books, "Cache should be empty before the first request.")

        response = self.client.get(self.books_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        cached_books = cache.get('books_list')
        self.assertIsNotNone(cached_books, "Cache should be populated after the first request.")
        self.assertEqual(cached_books, data, "Cached data should match the response data.")

        response2 = self.client.get(self.books_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        data2 = response2.json()

        self.assertEqual(data2, data, "Data from the second request should match the first.")
        Book.objects.create(
            title='Book 3',
            author='Author 3',
            isbn='3333',
            count_in_library=7,
            library='Main Library'
        )

        cached_books = cache.get('books_list')
        self.assertIsNone(cached_books, "Cache should be invalidated after adding a new book.")

        response3 = self.client.get(self.books_url)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        data3 = response3.json()

        cached_books = cache.get('books_list')
        self.assertIsNotNone(cached_books, "Cache should be repopulated after the request.")
        self.assertEqual(cached_books,
                         data3,
                         "Cached data should match the updated response data.")

        self.assertEqual(len(data3), 3, "The data should include all three books.")
        titles = [book['title'] for book in data3]
        self.assertIn('Book 3', titles, "The new book should be in the data.")

        self.assertNotEqual(data3,
                            data,
                            "The data should be updated and not equal to the previous data.")
