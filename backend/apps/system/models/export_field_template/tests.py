from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ExportFieldTemplateModel


class ExportFieldTemplateApiTests(APITestCase):
    url = "/api/system/export_field_template/"

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create(username="template-user", name="模板用户")
        cls.other_user = user_model.objects.create(
            username="other-template-user", name="其他模板用户"
        )
        cls.own_template = ExportFieldTemplateModel.objects.create(
            name="常用字段",
            api_path="/api/example/author/",
            fields=["name", "age"],
            creator=cls.user,
        )
        cls.other_template = ExportFieldTemplateModel.objects.create(
            name="其他用户模板",
            api_path="/api/example/author/",
            fields=["name"],
            creator=cls.other_user,
        )

    def setUp(self):
        self.client.force_authenticate(self.user)

    def test_list_only_returns_current_users_templates_for_api(self):
        response = self.client.get(
            self.url,
            {"paginate": "false", "api_path": "/api/example/author/"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data["data"]], [self.own_template.id])

    def test_create_binds_current_user(self):
        response = self.client.post(
            self.url,
            {
                "name": "基础字段",
                "api_path": "/api/example/author/",
                "fields": ["name", "gender"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        template = ExportFieldTemplateModel.objects.get(id=response.data["data"]["id"])
        self.assertEqual(template.creator, self.user)
        self.assertEqual(template.fields, ["name", "gender"])

    def test_duplicate_name_is_rejected_within_same_api(self):
        response = self.client.post(
            self.url,
            {
                "name": self.own_template.name,
                "api_path": self.own_template.api_path,
                "fields": ["name"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["success"])

    def test_cannot_update_or_delete_another_users_template(self):
        detail_url = f"{self.url}{self.other_template.id}/"
        update_response = self.client.put(
            detail_url,
            {
                "name": "越权修改",
                "api_path": self.other_template.api_path,
                "fields": ["name"],
            },
            format="json",
        )
        delete_response = self.client.delete(detail_url)

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertFalse(update_response.data["success"])
        self.assertFalse(delete_response.data["success"])
