from typing import Union, Type

from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import  ModelViewSet

from recipes.models import Favorite, ShoppingCart
from users.models import Follow


class CreateAndDeleteMixin:
    def create_and_delete_related(
            self: ModelViewSet,
            pk: int,
            klass: Union[Type[Favorite], Type[ShoppingCart], Type[Follow]],
            created_failed_message: str,
            delete_failed_message: str,
            field_to_create_or_delete_name: str,
    ):
        self_qs_obj = get_object_or_404(self.get_queryset(), pk=pk)
        kwargs = {
            'user': self.request.user,
            field_to_create_or_delete_name: self_qs_obj
        }
        if self.request.method == 'POST':

            try:
                klass.objects.create(
                    **kwargs
                )
            except IntegrityError:
                raise ValidationError({'errors': created_failed_message})

            context = self.get_serializer_context()
            serializer = self.get_serializer_class()

            response = Response(
                serializer(
                    instance=self_qs_obj, context=context
                ).data,
                status=status.HTTP_201_CREATED,
            )
        elif self.request.method == 'DELETE':
            klass_obj = klass.objects.filter(
                **kwargs
            ).first()

            if klass_obj is None:
                raise ValidationError({'errors': delete_failed_message})
            else:
                klass_obj.delete()

            response = Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ValidationError({'errors': 'Неверный метод запроса'})

        return response
