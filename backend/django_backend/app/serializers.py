from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from datetime import datetime, timezone, timedelta
from .models import Book, Reservation


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ['book_id']


class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Reservation
        fields = ['reservation_id',
                  'user',
                  'book',
                  'reserved_at',
                  'reserved_until',
                  'reservation_status',
                  'is_external']
        read_only_fields = ['reservation_id', 'reserved_at', 'reservation_status']
        extra_kwargs = {
            'reserved_until': {'required': False}
        }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Set reserved_until to one month from today
        validated_data['reserved_until'] = datetime.now(timezone.utc) + timedelta(days=30)
        return super().create(validated_data)


class ReturnBookSerializer(serializers.ModelSerializer):
    reservation_id = serializers.IntegerField(required=True)

    class Meta:
        model = Reservation
        fields = ['reservation_id']

    def validate(self, data):
        request_user = self.context['request'].user  # Get the user from the serializer context
        try:
            reservation = Reservation.objects.get(reservation_id=data['reservation_id'])
        except Reservation.DoesNotExist:
            reservation = None
            raise serializers.ValidationError("Reservation with this ID does not exist.")

        # Check if the user who is trying to return the book is the same who made the reservation
        if reservation.user != request_user:
            raise serializers.ValidationError("You do not have permission to return this book.")

        # Check if the reservation is already returned
        if not reservation.reservation_status or reservation is None:
            raise serializers.ValidationError("Reservation does not exist or already returned.")

        return data

    def update(self, instance, validated_data):
        instance.reservation_status = False  # Set the reservation as inactive
        instance.book.count_in_library += 1  # Increment the count of the book in the library
        instance.book.save()  # Save the updated book count
        instance.save()  # Save the reservation update
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'email']
