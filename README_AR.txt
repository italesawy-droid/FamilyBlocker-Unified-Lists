# FamilyBlockerUnified

هذا مستودع GitHub مساعد لبرنامج واحد يجمع بين:

1. حظر المواقع الإباحية عن طريق `hosts file`.
2. حظر أسماء الأفلام/المسلسلات والكلمات البحثية عن طريق قوائم `URLBlocklist` في `Chrome` و `Edge`.

## الفكرة الصحيحة

لا تجعل برنامج ويندوز يحتوي على القوائم داخله.  
البرنامج لاحقًا يحمّل الملف:

```text
familyblocker_manifest.json
```

ثم يعرض التصنيفات كـ `CheckBox`، وبعد اختيار التصنيفات يحمّل الملفات المطلوبة فقط من مجلد `public`.

## أهم الملفات

```text
familyblocker_manifest.json
familyblocker_categories.json
public/hosts/
public/domains/
public/titles/
public/keywords/
public/url_patterns/
```

## الملفات المتوافقة مع المشاريع القديمة

تم الإبقاء على أسماء ملفات في جذر المستودع لتسهيل الانتقال:

```text
familyblocker_hosts.txt
familyblocker_domains.txt
blocked_titles.txt
blocked_keywords.txt
generated_url_patterns.txt
blocked_titles_by_category.tsv
```

## تعديل التصنيفات

التصنيفات الأساسية موجودة هنا:

```text
config/categories.json
```

مصادر المواقع موجودة هنا:

```text
config/hosts_sources.tsv
```

تصنيفات الأفلام من Wikidata موجودة هنا:

```text
config/title_genres_enabled.tsv
```

الإضافات اليدوية:

```text
data/manual/domains.tsv
data/manual/titles.tsv
data/manual/keywords.tsv
```

الاستثناءات:

```text
data/allowlists/domains.txt
data/allowlists/titles.txt
```

## طريقة الرفع على GitHub

1. أنشئ مستودعًا جديدًا، ولا تمسح المستودعات القديمة الآن.
2. استخرج محتويات ملف ZIP على جهازك.
3. ارفع محتويات المجلد نفسها إلى GitHub، وليس ملف ZIP.
4. من تبويب `Actions` شغّل:

```text
Update FamilyBlocker Unified Lists
```

5. بعد التشغيل تأكد من وجود أو تحديث:

```text
familyblocker_manifest.json
public/hosts/
public/domains/
public/titles/
public/url_patterns/
```

## قاعدة مهمة لبرنامج ويندوز لاحقًا

عند تعديل ملف `hosts` يجب أن يكتب البرنامج داخل بلوك محدد فقط:

```text
# BEGIN FAMILYBLOCKERUNIFIED
0.0.0.0 example.com
# END FAMILYBLOCKERUNIFIED
```

ولا يلمس أي أسطر أخرى في ملف `hosts`.  
يجب كذلك إنشاء نسخة احتياطية قبل أي تعديل.

## ملاحظة دقة

حظر أسماء الأفلام والكلمات ليس فحصًا لمحتوى الصفحة نفسها.  
هو حظر روابط ونتائج بحث وأنماط URL في المتصفح، لذلك قد توجد نتائج خاطئة أو نقص في الحظر.  
لهذا السبب تم فصل التصنيفات حتى تستطيع فتح أو غلق كل جزء لاحقًا من البرنامج.
