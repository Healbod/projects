#!/usr/bin/env python
# coding: utf-8

import json
import bz2
import pandas as pd
from datetime import datetime
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_validate
from sklearn.preprocessing import StandardScaler


# Пример чтения матчей:
# with bz2.BZ2File('./data/data_matches/matches.jsonlines.bz2') as matches_file:
#     for line in matches_file:
#         match = json.loads(line)
#
#         break

# Подход 1: градиентный бустинг "в лоб"

# 1.Считайте таблицу с признаками из файла features.csv с помощью кода, приведенного выше. Удалите признаки, связанные с
# итогами матча (они помечены в описании данных как отсутствующие в тестовой выборке).
features = pd.read_csv('./data/features.csv', index_col='match_id')
X = features.drop(labels=['start_time', 'duration', 'radiant_win', 'tower_status_radiant', 'tower_status_dire',
       'barracks_status_radiant', 'barracks_status_dire'], axis=1)
y = features['radiant_win']

# 2. Проверьте выборку на наличие пропусков с помощью функции count(), которая для каждого столбца показывает число
# заполненных значений. Много ли пропусков в данных? Запишите названия признаков, имеющих пропуски, и попробуйте для
# любых двух из них дать обоснование, почему их значения могут быть пропущены.
for index,feature in enumerate(features.count()):
    if feature < features.shape[0]:
        print("В признаке {} отсутствуют {} знач.".format(features.axes[1][index],features.shape[0] - feature))

# 3. Замените пропуски на нули с помощью функции fillna(). На самом деле этот способ является предпочтительным для
# логистической регрессии, поскольку он позволит пропущенному значению не вносить никакого вклада в предсказание. Для
# деревьев часто лучшим вариантом оказывается замена пропуска на очень большое или очень маленькое значение — в этом
# случае при построении разбиения вершины можно будет отправить объекты с пропусками в отдельную ветвь дерева. Также
# есть и другие подходы — например, замена пропуска на среднее значение признака. Мы не требуем этого в задании, но
# при желании попробуйте разные подходы к обработке пропусков и сравните их между собой.
X = X.fillna(0)

# 4. Какой столбец содержит целевую переменную? Запишите его название.
print('Столбец {} содержит целевую переменную'.format(y.name))

# 5. Забудем, что в выборке есть категориальные признаки, и попробуем обучить градиентный бустинг над деревьями на
# имеющейся матрице "объекты-признаки". Зафиксируйте генератор разбиений для кросс-валидации по 5 блокам (KFold), не
# забудьте перемешать при этом выборку (shuffle=True), поскольку данные в таблице отсортированы по времени, и без
# перемешивания можно столкнуться с нежелательными эффектами при оценивании качества. Оцените качество градиентного
# бустинга (GradientBoostingClassifier) с помощью данной кросс-валидации, попробуйте при этом разное количество
# деревьев (как минимум протестируйте следующие значения для количества деревьев: 10, 20, 30). Долго ли настраивались
# классификаторы? Достигнут ли оптимум на испытанных значениях параметра n_estimators, или же качество, скорее всего,
# продолжит расти при дальнейшем его увеличении?
cv = KFold(n_splits=5, shuffle=True)
n_estimatorus = [10, 20, 30]
for n_est in n_estimatorus:
    start_time = datetime.now()
    clf_GBC = GradientBoostingClassifier(n_estimators=n_est)
    cv_results = cross_validate(clf_GBC, X, y=y, cv=cv, scoring='roc_auc')
    print('Время кросс-валидации для {} деревьев составляет {}'.format(n_est, datetime.now() - start_time))
    print('при этом качество обучения получилось равны {}'.format(round(cv_results['test_score'].mean(), 6)))

# Подход 2: логистическая регрессия

# 1. Оцените качество логистической регрессии (sklearn.linear_model.LogisticRegression с L2-регуляризацией) с помощью
# кросс-валидации по той же схеме, которая использовалась для градиентного бустинга. Подберите при этом лучший параметр
# регуляризации (C). Какое наилучшее качество у вас получилось? Как оно соотносится с качеством градиентного бустинга?
# Чем вы можете объяснить эту разницу? Быстрее ли работает логистическая регрессия по сравнению с градиентным бустингом?
scaled = StandardScaler()
X_scaled = scaled.fit_transform(X)

# start_time = datetime.now()
LR = LogisticRegression(penalty='l2')
clf_LR = GridSearchCV(LR, {'C': [0.001, 0.01, 0.1, 1, 10, 1e2, 1e3]}, cv=cv, scoring='roc_auc')
clf_LR.fit(X_scaled, y=y)
print('Лучший параметр регуляризации C составляет {}'.format(clf_LR.best_params_['C']))
print('Время кросс-валидации логической регрессии составляет {}'.format(datetime.now() - start_time))
print('при это качество обучения получилось равны {}'.format(round(clf_LR.cv_results_['mean_test_score'].mean(), 6)))

# 2. Среди признаков в выборке есть категориальные, которые мы использовали как числовые, что вряд ли является хорошей
# идеей. Категориальных признаков в этой задаче одиннадцать: lobby_type и r1_hero, r2_hero, ..., r5_hero, d1_hero,
# d2_hero, ..., d5_hero. Уберите их из выборки, и проведите кросс-валидацию для логистической регрессии на новой
# выборке с подбором лучшего параметра регуляризации. Изменилось ли качество? Чем вы можете это объяснить?
X_clear = X.drop(labels=['lobby_type', 'r1_hero', 'r2_hero', 'r3_hero', 'r4_hero', 'r5_hero',
                   'd1_hero', 'd2_hero', 'd3_hero', 'd4_hero', 'd5_hero'], axis=1)
scaled_clear = StandardScaler()
X_scaled_clear = scaled_clear.fit_transform(X_clear)

start_time = datetime.now()
clf_LR_clear = GridSearchCV(LR, {'C': [0.001, 0.01, 0.1, 1, 10, 1e2, 1e3]}, cv=cv, scoring='roc_auc')
clf_LR_clear.fit(X_scaled_clear, y=y)
print('Лучший параметр регуляризации без категориальных параметров C составляет {}'.format(clf_LR.best_params_['C']))
print('Время кросс-валидации логической регрессии без кат параметров составляет {}'.format(datetime.now() - start_time))
print('при это качество обучения получилось равны {}'.format(round(clf_LR.cv_results_['mean_test_score'].mean(), 6)))


# 3. На предыдущем шаге мы исключили из выборки признаки rM_hero и dM_hero, которые показывают, какие именно герои
# играли за каждую команду. Это важные признаки — герои имеют разные характеристики, и некоторые из них выигрывают
# чаще, чем другие. Выясните из данных, сколько различных идентификаторов героев существует в данной игре (вам может
# пригодиться фукнция unique или value_counts).
X_heroes = X.loc[:, ['r1_hero', 'r2_hero', 'r3_hero', 'r4_hero', 'r5_hero',
                    'd1_hero', 'd2_hero', 'd3_hero', 'd4_hero', 'd5_hero']]
for i in range(X_heroes.shape[1]):
    if i == 0:
        df_herous = pd.DataFrame(np.zeros((len(X_heroes.iloc[:, i].value_counts()), X_heroes.shape[1])),
                           index=X_heroes.iloc[:, i].value_counts().sort_index().index,
                           columns=X_heroes.columns)
        df_herous.iloc[:, i] = X_heroes.iloc[:, i].value_counts().sort_index()
    else:
        df_herous.iloc[:, i] = X_heroes.iloc[:, i].value_counts().sort_index()
print('Кол-во уникальных герое составляет {} при этом максимальный ID = {}'
      .format(df_herous.shape[0], df_herous.index[-1]))

# 4. Воспользуемся подходом "мешок слов" для кодирования информации о героях. Пусть всего в игре имеет N различных
# героев. Сформируем N признаков, при этом i-й будет равен нулю, если i-й герой не участвовал в матче; единице, если
# i-й герой играл за команду Radiant; минус единице, если i-й герой играл за команду Dire. Ниже вы можете найти код,
# который выполняет данной преобразование. Добавьте полученные признаки к числовым, которые вы использовали во втором
# пункте данного этапа.
X_pick = np.zeros((X_heroes.shape[0], df_herous.index[-1]))
for i, match_id in enumerate(X_heroes.index):
    for p in range(5):
        X_pick[i, X_heroes.loc[match_id, 'r%d_hero' % (p+1)]-1] = 1
        X_pick[i, X_heroes.loc[match_id, 'd%d_hero' % (p+1)]-1] = -1
X_sc_cl_df = np.hstack((X_scaled_clear,X_pick))

# 5. Проведите кросс-валидацию для логистической регрессии на новой выборке с подбором лучшего параметра регуляризации.
# Какое получилось качество? Улучшилось ли оно? Чем вы можете это объяснить?
start_time = datetime.now()
clf_LR_cl_h = GridSearchCV(LR, {'C': [0.001, 0.01, 0.1, 1, 10, 1e2, 1e3]}, cv=cv, scoring='roc_auc')
clf_LR_cl_h.fit(X_sc_cl_df, y=y)
print('Лучший параметр регуляризации использую "мешок слов" C составляет {}'
      .format(clf_LR_cl_h.best_params_['C']))
print('Время кросс-валидации логической регрессии использую "мешок слов" составляет {}'
      .format(datetime.now() - start_time))
print('при это качество обучения получилось равны {}'
      .format(round(clf_LR_cl_h.cv_results_['mean_test_score'].mean(), 6)))


# 6. Постройте предсказания вероятностей победы команды Radiant для тестовой выборки с помощью лучшей из изученных
# моделей (лучшей с точки зрения AUC-ROC на кросс-валидации). Убедитесь, что предсказанные вероятности адекватные —
# находятся на отрезке [0, 1], не совпадают между собой (т.е. что модель не получилась константной).
feature_test = pd.read_csv('./data/features_test.csv', index_col='match_id')

X_test = feature_test.drop(labels=['start_time','lobby_type', 'r1_hero', 'r2_hero', 'r3_hero', 'r4_hero', 'r5_hero',
                   'd1_hero', 'd2_hero', 'd3_hero', 'd4_hero', 'd5_hero'], axis=1)
X_test = X_test.fillna(0)
X_test_scaled = scaled_clear.transform(X_test)
X_heroes_test = feature_test.loc[:, ['r1_hero', 'r2_hero', 'r3_hero', 'r4_hero', 'r5_hero',
                                'd1_hero', 'd2_hero', 'd3_hero', 'd4_hero', 'd5_hero']]

X_test_pick = np.zeros((X_heroes_test.shape[0], df_herous.index[-1]))
for i, match_id in enumerate(X_heroes_test.index):
    for p in range(5):
        X_test_pick[i, X_heroes_test.loc[match_id, 'r%d_hero' % (p+1)]-1] = 1
        X_test_pick[i, X_heroes_test.loc[match_id, 'd%d_hero' % (p+1)]-1] = -1
X_test_sc_cl_df = np.hstack((X_test_scaled,X_test_pick))


pred = clf_LR_cl_h.predict_proba(X_test_sc_cl_df)[:, 1]
pred_df = pd.Series(pred, index=feature_test.index, name='radiant_win')
print(pred_df)
print('Максимальное значение на тестовой выборке получилось равным {}, минимальное - {}'
      .format(round(pred_df.max(), 4), round(pred_df.min(), 4)))
pred_df.to_csv(r'pred.csv', header=True)


