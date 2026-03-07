PlusProgress API
================
API для онлайн школы PlusProgress

**Version:** 1.0.0

<br/><br/><br/>
# **API**<br/>

<br/>
### /api/deposits/
---
## ***GET***
**Description:** API для депозитов

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для депозитов

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/deposits/{id}/
---
## ***GET***
**Description:** API для депозитов

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Депозит. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для депозитов

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Депозит. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для депозитов

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Депозит. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для депозитов

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Депозит. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/feedbacks/
---
## ***GET***
**Description:** API для отзывов о уроках

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для отзывов о уроках

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/feedbacks/{id}/
---
## ***GET***
**Description:** API для отзывов о уроках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Оценка урока. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для отзывов о уроках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Оценка урока. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для отзывов о уроках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Оценка урока. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для отзывов о уроках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Оценка урока. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/group-enrollments/
---
## ***GET***
**Description:** API для записей на групповые уроки

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для записей на групповые уроки

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/group-enrollments/{id}/
---
## ***GET***
**Description:** API для записей на групповые уроки

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Запись на группу. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для записей на групповые уроки

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Запись на группу. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для записей на групповые уроки

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Запись на группу. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для записей на групповые уроки

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Запись на группу. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/group-lessons/
---
## ***GET***
**Description:** API для групповых уроков

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для групповых уроков

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/group-lessons/{id}/
---
## ***GET***
**Description:** API для групповых уроков

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Групповое занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для групповых уроков

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Групповое занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для групповых уроков

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Групповое занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для групповых уроков

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Групповое занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/group-lessons/{id}/enroll/
---
## ***POST***
**Description:** Записать ученика на групповой урок

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Групповое занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/homeworks/
---
## ***GET***
**Description:** API для домашних заданий

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для домашних заданий

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/homeworks/{id}/
---
## ***GET***
**Description:** API для домашних заданий

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Домашнее задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для домашних заданий

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Домашнее задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для домашних заданий

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Домашнее задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для домашних заданий

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Домашнее задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/homeworks/{id}/submit/
---
## ***POST***
**Description:** Сдать домашнее задание

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Домашнее задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/lesson-reports/
---
## ***GET***
**Description:** API для отчетов о уроках

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для отчетов о уроках

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/lesson-reports/{id}/
---
## ***GET***
**Description:** API для отчетов о уроках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Отчет о занятии. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для отчетов о уроках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Отчет о занятии. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для отчетов о уроках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Отчет о занятии. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для отчетов о уроках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Отчет о занятии. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/lessons/
---
## ***GET***
**Description:** API для уроков

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для уроков

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/lessons/{id}/
---
## ***GET***
**Description:** Получение конкретного урока с проверкой прав

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для уроков

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для уроков

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для уроков

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Занятие. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/login/
---
## ***POST***
**Responses**

| Code | Description |
| ---- | ----------- |
| 200 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/materials/
---
## ***GET***
**Description:** API для методических материалов

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для методических материалов

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/materials/{id}/
---
## ***GET***
**Description:** API для методических материалов

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Методический материал. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для методических материалов

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Методический материал. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для методических материалов

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Методический материал. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для методических материалов

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Методический материал. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/notifications/
---
## ***GET***
**Description:** API для уведомлений

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для уведомлений

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/notifications/{id}/
---
## ***GET***
**Description:** API для уведомлений

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Уведомление. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для уведомлений

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Уведомление. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для уведомлений

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Уведомление. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для уведомлений

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Уведомление. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/notifications/{id}/mark_read/
---
## ***POST***
**Description:** API для уведомлений

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Уведомление. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/notifications/mark_all_read/
---
## ***POST***
**Description:** API для уведомлений

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/payment-requests/
---
## ***GET***
**Description:** API для запросов на выплаты

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для запросов на выплаты

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/payment-requests/{id}/
---
## ***GET***
**Description:** API для запросов на выплаты

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Запрос выплаты. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для запросов на выплаты

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Запрос выплаты. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для запросов на выплаты

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Запрос выплаты. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для запросов на выплаты

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Запрос выплаты. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/payments/
---
## ***GET***
**Description:** API для платежей

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для платежей

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/payments/{id}/
---
## ***GET***
**Description:** API для платежей

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Платеж. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для платежей

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Платеж. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для платежей

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Платеж. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для платежей

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Платеж. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/register/
---
## ***POST***
**Description:** Регистрация нового пользователя

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| Bearer | [object Object] |

<br/>
### /api/schedule-templates/
---
## ***GET***
**Description:** API для шаблонов расписания

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для шаблонов расписания

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/schedule-templates/{id}/
---
## ***GET***
**Description:** API для шаблонов расписания

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Шаблон расписания. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для шаблонов расписания

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Шаблон расписания. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для шаблонов расписания

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Шаблон расписания. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для шаблонов расписания

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Шаблон расписания. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/schedule-templates/{id}/generate/
---
## ***POST***
**Description:** Сгенерировать уроки из шаблона

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Шаблон расписания. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/student-notes/
---
## ***GET***
**Description:** API для заметок об учениках

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для заметок об учениках

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/student-notes/{id}/
---
## ***GET***
**Description:** API для заметок об учениках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Заметка об ученике. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для заметок об учениках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Заметка об ученике. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для заметок об учениках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Заметка об ученике. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для заметок об учениках

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Заметка об ученике. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/student-prices/
---
## ***GET***
**Description:** API для индивидуальных цен

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для индивидуальных цен

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/student-prices/{id}/
---
## ***GET***
**Description:** API для индивидуальных цен

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Цена для ученика. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для индивидуальных цен

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Цена для ученика. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для индивидуальных цен

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Цена для ученика. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для индивидуальных цен

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Цена для ученика. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/students/
---
## ***GET***
**Description:** API для учеников

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для учеников

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/students/{id}/
---
## ***GET***
**Description:** API для учеников

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Ученик. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для учеников

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Ученик. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для учеников

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Ученик. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для учеников

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Ученик. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/students/me/
---
## ***GET***
**Description:** Получить данные текущего ученика

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/submissions/
---
## ***GET***
**Description:** API для сданных заданий

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для сданных заданий

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/submissions/{id}/
---
## ***GET***
**Description:** API для сданных заданий

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Выполненное задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для сданных заданий

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Выполненное задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для сданных заданий

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Выполненное задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для сданных заданий

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Выполненное задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/submissions/{id}/check/
---
## ***POST***
**Description:** Проверить задание (для учителя)

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Выполненное задание. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/teachers/
---
## ***GET***
**Description:** API для учителей

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для учителей

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/teachers/{id}/
---
## ***GET***
**Description:** API для учителей

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Учитель. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для учителей

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Учитель. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для учителей

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Учитель. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для учителей

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Учитель. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/trial-requests/
---
## ***GET***
**Description:** API для заявок на пробный урок

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***POST***
**Description:** API для заявок на пробный урок

**Responses**

| Code | Description |
| ---- | ----------- |
| 201 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

<br/>
### /api/trial-requests/{id}/
---
## ***GET***
**Description:** API для заявок на пробный урок

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Заявка на пробный урок. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PUT***
**Description:** API для заявок на пробный урок

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Заявка на пробный урок. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***PATCH***
**Description:** API для заявок на пробный урок

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Заявка на пробный урок. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 200 |  |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |

## ***DELETE***
**Description:** API для заявок на пробный урок

**Parameters**

| Name | Located in | Required | Schema | Description |
| ---- | ---------- | -------- | ------ | ----------- |
| id | path | Yes | integer | A unique integer value identifying this Заявка на пробный урок. |

**Responses**

| Code | Description |
| ---- | ----------- |
| 204 | No response body |

**Security**

| Security Schema | Scopes |
| --- | --- |
| tokenAuth | |
| Bearer | [object Object] |
