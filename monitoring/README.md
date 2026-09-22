# RFP monitoring — Docker validation stage

هذه الحزمة تخص السيرفر الجديد aidc-t06 فقط. لا تستخدم إعدادات سيرفر amr السابق.
أربعة ملفات تشغيل/توثيق؛ لا توجد صورة مخصصة ولا تثبيت حزم على المضيف.

## الحالة

- Docker Compose 2.29.2 موجود. المصدّران يستجيبان محليًا على 9100 و9400.
- المنفذان 3000 و9090 كانا متاحين عند الفحص؛ يعاد فحصهما قبل التشغيل.
- الصور محددة الإصدار: Prometheus 3.14.0 وGrafana 13.2.2. سحب الصور وفحصها وتشغيلها يتم على السيرفر ولم ينفذها المساعد.
- مقاييس GPU utilization وframebuffer والـCPU/RAM تستخدم أسماء المصدّرات القياسية؛ توفرها الفعلي يحتاج فحص queries بعد التشغيل. غيابها يظهر No data.
- لم يحدد مصدر مقاييس النموذج؛ لا توجد أرقام اصطناعية لـTTFT أو نجاح الطلبات أو الدقة.
- إعدادات المصادر ومزود الداشبورد مضمّنة داخل compose.yaml لتقليل الملفات.

## 1. فحص الإعداد دون تشغيل خدمات دائمة

من مجلد المشروع، بعد رفع الأرشيف. الأمر يرفض الفك إذا كان مجلد monitoring موجودًا؛ عند وجوده لا تحذفه ولا تستبدله قبل مراجعته.

```bash
test ! -e monitoring && python3 -m zipfile -e rfp-monitoring.zip .
cd monitoring
ls -lh
GRAFANA_ADMIN_PASSWORD=validation-only docker compose config --quiet
GRAFANA_ADMIN_PASSWORD=validation-only docker compose pull
GRAFANA_ADMIN_PASSWORD=validation-only docker compose run --rm --no-deps --entrypoint /bin/promtool prometheus check config /etc/prometheus/prometheus.yml
```

قيمة validation-only مخصصة لفحص الإعداد وسحب الصور وفحص Prometheus؛ لا تستخدمها لتشغيل Grafana.
promtool يشغّل حاوية مؤقتة للفحص فقط، ولا يشغّل خادم Prometheus. Docker قد ينشئ volume المشروع أثناء هذا الفحص.
لا تنفذ الخطوة التالية إذا فشل أي فحص. يحظر استبدال الإصدارات بـlatest لمعالجة فشل سحب صورة.

## 2. التشغيل بعد نجاح الفحوص

تحقق أن هذا المشروع لا توجد له حاويات سابقة، وأن المنافذ ما زالت متاحة:

```bash
docker ps -a --filter label=com.docker.compose.project=rfp-monitoring
ss -lnt '( sport = :3000 or sport = :9090 )'
```

إذا ظهرت حاويات سابقة أو منافذ مستخدمة، توقف وراجعها. عيّن كلمة مرور قوية في نفس الطرفية، دون إرسالها للمحادثة:

```bash
read -rsp 'Choose Grafana admin password: ' GRAFANA_ADMIN_PASSWORD
export GRAFANA_ADMIN_PASSWORD
```

كلمة المرور تستخدم لتهيئة قاعدة Grafana الجديدة فقط؛ تغيير المتغير لا يعيد تعيين حساب موجود. يمكن لمسؤولي Docker رؤية متغيرات الحاويات، لذلك لا تستخدم كلمة مرور حسابك الشخصي.

```bash
docker compose up -d
docker compose ps
curl --noproxy '*' --max-time 5 -fsS http://127.0.0.1:9090/-/ready
curl --noproxy '*' --max-time 5 -fsS http://127.0.0.1:3000/api/health
```

إذا كانت الخدمة لا تزال تبدأ، انتظر قليلًا وأعد فحص الصحة فقط؛ لا تعيد الإنشاء.
فحص الأهداف بعد الجاهزية:

```bash
curl --noproxy '*' --max-time 10 -fsS 'http://127.0.0.1:9090/api/v1/query?query=up'
```

المتوقع node وdcgm وprometheus بقيمة 1. وجود up=1 يثبت جمع المقاييس، وليس توفر كل أسماء المقاييس التي تحتاجها اللوحة.

## 3. الوصول

الخدمتان تستمعان على 127.0.0.1 فقط. في VS Code افتح Ports، وحوّل منفذ 3000 عبر الاتصال الحالي مع إبقاء الوصول خاصًا. افتح عنوان المنفذ المحوّل الذي يعرضه VS Code؛ ليس بالضرورة localhost:3000 على جهازك.

سجّل الدخول باسم admin وكلمة المرور التي اخترتها. افتح Dashboards ثم RFP Monitoring ثم RFP AI — Infrastructure Monitoring. انتظر دقيقة لجمع عينات كافية لمعدلات الاستخدام.

اللوحة مؤقتًا للبنية التحتية. لا يجوز وصفها بأنها لوحة مراقبة النموذج المكتملة. سنضيف لوحات النموذج إلى dashboard.json نفسه بعد التحقق من endpoint وأسماء metrics وlabels وأنواع histograms.

## التنظيم والتراجع

الصور الرسمية تعمل بشبكة المضيف على Linux للوصول إلى المصدّرين في loopback. الاستماع نفسه محلي. لا يتغير Docker الخاص بالمصدّرين ولا Kubernetes ولا تطبيق الفريق.
تستخدم الخدمات volumes بأسماء تبدأ بـrfp-monitoring_. مدة الاحتفاظ في Prometheus ثلاثة أيام وحجم blocks المستهدف 1GB؛ WAL والملفات المؤقتة قد تستهلك مساحة إضافية. حد الذاكرة الإجمالي للحاويتين 1.5GiB، وحد CPU لكل منهما واحد؛ هذه حدود وليست حجوزات.

لإيقاف الحاويتين الجديدتين مع الاحتفاظ بالبيانات:

```bash
GRAFANA_ADMIN_PASSWORD=validation-only docker compose stop
```

لا تستخدم down -v لأنه يحذف بيانات المراقبة. لا تحذف المصدّرين الحاليين.
تعديل الداشبورد في dashboard.json، ومصادر الجمع في prometheus.yml. مراجعة التغييرات وفحصها يسبقان إعادة تحميلها.
عند الانتقال إلى Kubernetes سنعيد استخدام ملفي Prometheus والداشبورد؛ host loopback الحالي ليس إعدادًا صالحًا تلقائيًا داخل Pods، لذا يلزم تعيين أهداف الجمع من جديد وفحص التخزين والصلاحيات.

## مصادر الإصدارات والتشغيل

- https://github.com/prometheus/prometheus/releases/tag/v3.14.0
- https://grafana.com/grafana/download/13.2.2
- https://grafana.com/docs/grafana/latest/administration/provisioning/

تحقق محلي: JSON وهيكل الداشبورد. فحص Compose وpromtool والاستيراد والبيانات الحية يجب إتمامه على السيرفر قبل اعتبار الحزمة ناجحة.
