from django.db import models

class Book(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    author = models.CharField(
        max_length=100,
        verbose_name="Автор"
    )
    year = models.IntegerField(
        verbose_name="Год издания"
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="Прочитана"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлена"
    )

    def __str__(self):
        return f"{self.title} - {self.author}"

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"