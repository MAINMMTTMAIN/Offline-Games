import pygame
import os
import time
import random
from base_game import BaseGame
from main import resource_path, get_base_path
from persian_utils import render_persian_text, reshape_persian

# ─────────────────────────── TEXT BANK ────────────────────────────────────────

TEXTS = {
    "en": {
        "easy": [
            "The sun rises in the east and sets in the west, painting the sky with beautiful shades of orange and pink every single day. Nature has its own way of showing us the beauty of life. Take a moment to appreciate the small things around you.",
            "Walking through the park on a sunny afternoon can be one of the most relaxing experiences. You can hear the birds singing, feel the gentle breeze on your face, and see children playing happily on the green grass. It is a perfect day.",
            "Technology has made our lives incredibly convenient. We can now communicate with people across the globe in a matter of seconds. Mobile phones and computers are essential tools that help us learn, work, and stay connected with our loved ones.",
            "Reading books is a wonderful habit that opens up new worlds. Whether it is fiction, history, or science, every book holds a treasure of knowledge. Taking time to read every day improves your vocabulary and broadens your perspective.",
            "A healthy lifestyle involves eating nutritious food, exercising regularly, and getting enough sleep. Drinking plenty of water and avoiding junk food can make a huge difference in how you feel. Your body is your temple, so take good care of it.",
            "Learning a new skill can be challenging at first, but with practice, it becomes easier. Consistency is the key to success. Do not be afraid to make mistakes, because they are stepping stones to mastering whatever you are trying to learn.",
            "Friendship is one of the most valuable gifts in life. True friends support you in difficult times and celebrate your successes. Building strong relationships requires trust, honesty, and spending quality time together.",
            "The ocean is vast and full of mysteries. Millions of different species live underwater, many of which we have not even discovered yet. Protecting marine life and keeping the oceans clean is vital for the future of our planet.",
            "Cooking at home can be both fun and rewarding. You get to choose your own ingredients and experiment with different flavors. Plus, sharing a home-cooked meal with family and friends creates beautiful memories around the dinner table.",
            "Music has the power to change our mood instantly. A cheerful song can make you want to dance, while a slow melody can help you relax after a long day. Everyone has their own favorite genre that speaks to their heart."
        ],
        "medium": [
            "The industrial revolution marked a major turning point in history. Almost every aspect of daily life was influenced in some way. Average income and population began to exhibit unprecedented sustained growth. Factories replaced hand tools, and steam engines transformed transportation, leading to the modern, fast-paced world we live in today.",
            "Space exploration has always fascinated humanity. From the first moon landing to the deployment of rovers on Mars, our understanding of the universe continues to expand. Telescopes capture breathtaking images of distant galaxies, proving just how small our world really is in the grand cosmic scheme.",
            "Artificial intelligence is rapidly changing the landscape of technology and business. Machine learning algorithms can analyze vast amounts of data to predict trends, automate repetitive tasks, and even generate creative content. However, this progress also brings up important ethical discussions regarding privacy and employment.",
            "Climate change is a pressing global issue that requires immediate action. The increasing levels of greenhouse gases are causing temperatures to rise, melting ice caps, and leading to extreme weather patterns. Transitioning to renewable energy sources like solar and wind power is crucial to mitigating these devastating effects.",
            "The history of art reflects the evolution of human thought and culture. From prehistoric cave paintings to Renaissance masterpieces and modern abstract works, artists have always found unique ways to express their emotions. Museums and galleries preserve these treasures, allowing us to connect with the past on a visual level.",
            "Effective communication is the cornerstone of any successful organization. Whether it is written emails, formal presentations, or casual team meetings, conveying your ideas clearly prevents misunderstandings. Active listening is equally important, as it shows respect and fosters a collaborative working environment.",
            "The concept of mindfulness involves staying present and fully engaging with the current moment. In our fast-paced modern society, people often find themselves stressing about the future or dwelling on the past. Practicing mindfulness through meditation or deep breathing exercises can significantly reduce anxiety and improve focus.",
            "Cryptocurrency and blockchain technology have introduced a new paradigm in the financial sector. By operating on decentralized networks, digital currencies aim to provide secure and transparent transactions without the need for traditional banks. While highly volatile, this technology holds the potential to revolutionize digital ownership.",
            "Regular physical exercise not only strengthens muscles and improves cardiovascular health, but it also has profound effects on mental well-being. Physical activity releases endorphins, which are natural mood lifters. Incorporating just thirty minutes of moderate exercise into your daily routine can yield long-term health benefits.",
            "The architectural wonders of the ancient world continue to baffle modern engineers. Structures like the Great Pyramid of Giza and the Colosseum in Rome were built with such precision that they have withstood the test of time for millennia. Studying these monuments gives us insight into the incredible ingenuity of ancient civilizations."
        ],
        "hard": [
            "Photosynthesis is the fundamental biological process by which green plants, algae, and certain bacteria transform light energy into chemical energy. During this process, carbon dioxide and water are converted into glucose and oxygen, utilizing sunlight absorbed by chlorophyll. This not only forms the base of the global food web but also plays a critical role in maintaining the oxygen levels in the Earth's atmosphere, regulating the climate, and sustaining virtually all life forms on our planet.",
            "The theory of general relativity, published by Albert Einstein in 1915, revolutionized our understanding of gravity. Unlike classical mechanics, which viewed gravity as a simple force of attraction between masses, relativity describes it as the curvature of spacetime caused by the presence of mass and energy. This framework has successfully predicted phenomena such as the bending of light by massive objects, the orbital decay of binary pulsars, and the existence of black holes.",
            "Navigating the complexities of international trade law requires a deep understanding of bilateral agreements, tariffs, and customs regulations. Corporations expanding globally must ensure compliance with the World Trade Organization standards while also adapting to local legal frameworks. Failure to adhere to these stringent regulations can result in severe financial penalties, embargoes, and a significant loss of corporate reputation in the highly competitive global market.",
            "Neurological research has demonstrated that the human brain possesses a remarkable characteristic known as neuroplasticity. This refers to the brain's ability to reorganize itself by forming new neural connections throughout life in response to learning, experience, or following an injury. Understanding neuroplasticity has profound implications for cognitive rehabilitation therapies, educational methodologies, and our overall comprehension of memory retention and cognitive decline in aging populations.",
            "The rapid proliferation of digital media has fundamentally altered the paradigm of contemporary journalism. Traditional print publications are increasingly challenged by real-time news aggregators, social media platforms, and independent digital creators. This democratization of information distribution allows for immediate global communication, yet it concurrently introduces significant challenges regarding information verification, the spread of misinformation, and the preservation of journalistic integrity.",
            "Quantum computing represents a monumental leap forward in computational capabilities. By leveraging the principles of quantum mechanics, such as superposition and entanglement, quantum computers can process complex algorithms exponentially faster than classical supercomputers. This emerging technology holds the promise of revolutionizing fields ranging from cryptographic security and molecular modeling to complex logistical optimization and advanced artificial intelligence development.",
            "The intricate ecosystem of a coral reef is often referred to as the rainforest of the sea due to its staggering biodiversity. These underwater structures, built from the calcium carbonate secretions of corals, provide habitat, shelter, and breeding grounds for a quarter of all marine species. Unfortunately, rising ocean temperatures and increased acidification pose existential threats to these delicate ecosystems, leading to widespread coral bleaching and devastating ecological consequences.",
            "In the realm of software engineering, the implementation of robust continuous integration and continuous deployment pipelines is essential for maintaining code quality in large-scale applications. By automating the testing and deployment processes, development teams can rapidly identify bugs, seamlessly integrate collaborative code contributions, and deliver updates to end-users with minimal downtime. This methodology necessitates rigorous version control and comprehensive automated testing frameworks.",
            "The philosophy of existentialism emphasizes individual existence, freedom, and choice. It posits that humans define their own meaning in life, and try to make rational decisions despite existing in an irrational universe. Prominent figures like Jean-Paul Sartre and Albert Camus explored themes of absurdity, authenticity, and the weight of personal responsibility, arguing that we are ultimately the authors of our own destiny, free from deterministic constraints.",
            "Epidemiological modeling plays a critical role in public health management during infectious disease outbreaks. By utilizing complex mathematical frameworks, such as the Susceptible-Infectious-Recovered (SIR) model, researchers can simulate the potential spread of pathogens within a population. These predictive models allow governments and health organizations to make informed decisions regarding resource allocation, vaccination strategies, and the implementation of effective social distancing interventions."
        ]
    },
    "fa": {
        "easy": [
            "آب و هوای امروز بسیار خوب است و خورشید در آسمان می‌درخشد. قدم زدن در این هوای مطبوع می‌تواند انرژی زیادی به انسان بدهد. بیایید از این لحظات زیبا لذت ببریم و شکرگزار باشیم.",
            "کتاب خواندن یکی از بهترین راه‌ها برای افزایش دانش و آگاهی است. هر کتابی که می‌خوانیم، دریچه‌ای جدید به روی ذهن ما باز می‌کند و به ما کمک می‌کند تا دنیا را از دیدگاه‌های مختلفی ببینیم.",
            "ورزش کردن به صورت منظم نه تنها باعث سلامت جسم می‌شود، بلکه روحیه ما را نیز شاداب می‌کند. حتی نیم ساعت پیاده‌روی در روز می‌تواند تاثیرات بسیار مثبتی بر روی کیفیت زندگی ما داشته باشد.",
            "احترام به دیگران و مهربانی کردن، از مهم‌ترین ویژگی‌های یک انسان موفق است. وقتی با دیگران با خوش‌رویی برخورد می‌کنیم، در واقع حس خوبی را به خودمان نیز هدیه می‌دهیم.",
            "تکنولوژی در سال‌های اخیر پیشرفت‌های چشمگیری داشته است. گوشی‌های هوشمند و اینترنت کارها را بسیار راحت‌تر کرده‌اند، اما باید مراقب باشیم که بیش از حد به آن‌ها وابسته نشویم.",
            "خوردن غذاهای سالم و میوه‌های تازه برای حفظ سلامتی بدن بسیار ضروری است. ما باید سعی کنیم مصرف شیرینی‌جات و غذاهای چرب را کاهش دهیم تا بدنی قوی و سالم داشته باشیم.",
            "خانواده مهم‌ترین بخش زندگی هر فرد است. وقت گذراندن با پدر، مادر و خواهر و برادر، خاطرات زیبایی را می‌سازد که تا آخر عمر در ذهن ما باقی می‌مانند و به ما آرامش می‌دهند.",
            "یادگیری یک زبان جدید می‌تواند بسیار هیجان‌انگیز باشد. این کار نه تنها حافظه را تقویت می‌کند، بلکه به ما این امکان را می‌دهد که با فرهنگ‌ها و مردم سایر نقاط جهان آشنا شویم.",
            "موفقیت به راحتی به دست نمی‌آید و نیازمند تلاش و پشتکار فراوان است. اگر در مسیر رسیدن به اهدافمان با شکست روبرو شدیم، نباید ناامید شویم، بلکه باید از آن درس بگیریم.",
            "طبیعت پر از زیبایی‌های شگفت‌انگیز است. از جنگل‌های سرسبز گرفته تا کوه‌های بلند و اقیانوس‌های پهناور، همه نشان‌دهنده عظمت جهان هستند. وظیفه ما محافظت از این زیبایی‌هاست."
        ],
        "medium": [
            "تاریخ ایران باستان پر از فراز و نشیب‌ها و امپراتوری‌های بزرگی مانند هخامنشیان و ساسانیان است. این تمدن‌های عظیم دستاوردهای شگرفی در زمینه‌های معماری، قانون‌گذاری و هنر داشتند که هنوز هم مورد تحسین جهانیان قرار می‌گیرد. مطالعه این تاریخ غنی به ما کمک می‌کند تا ریشه‌های فرهنگی خود را بهتر بشناسیم.",
            "در دنیای امروزی، سواد رسانه‌ای به یکی از مهارت‌های ضروری تبدیل شده است. با وجود شبکه‌های اجتماعی و حجم انبوه اطلاعات، توانایی تشخیص اخبار درست از شایعات و اطلاعات نادرست، به افراد کمک می‌کند تا تصمیم‌گیری‌های منطقی‌تری داشته باشند و تحت تاثیر موج‌های رسانه‌ای قرار نگیرند.",
            "هوش مصنوعی دیگر یک داستان علمی تخیلی نیست، بلکه بخشی جدایی‌ناپذیر از زندگی روزمره ما شده است. از دستیارهای صوتی در گوشی‌های موبایل تا الگوریتم‌های پیچیده‌ای که در پزشکی برای تشخیص بیماری‌ها استفاده می‌شوند، همه نشان از تحولی بزرگ دارند که نحوه کار و زندگی انسان‌ها را برای همیشه تغییر می‌دهد.",
            "توسعه پایدار به معنای استفاده از منابع طبیعی به گونه‌ای است که نیازهای نسل امروز برطرف شود بدون آنکه توانایی نسل‌های آینده برای تامین نیازهایشان به خطر بیفتد. حفظ محیط زیست، کاهش گازهای گلخانه‌ای و روی آوردن به انرژی‌های تجدیدپذیر مانند انرژی خورشیدی و بادی، از اصول اساسی این نوع توسعه هستند.",
            "ادبیات کهن فارسی گنجینه‌ای از حکمت و اخلاق است. شاعران بزرگی همچون سعدی، حافظ و فردوسی، مفاهیم عمیق انسانی مانند عشق، عدالت، فداکاری و گذشت را در قالب اشعاری بی‌نظیر بیان کرده‌اند. خواندن این آثار نه تنها دایره لغات ما را گسترش می‌دهد، بلکه به ما درس درست زندگی کردن می‌آموزد.",
            "مدیریت زمان یکی از کلیدی‌ترین عوامل در دستیابی به موفقیت‌های تحصیلی و شغلی است. افرادی که می‌توانند برنامه‌ریزی دقیقی برای روزهای خود داشته باشند و اولویت‌هایشان را به درستی مشخص کنند، معمولاً با استرس کمتری روبرو می‌شوند و بازدهی بسیار بالاتری نسبت به سایرین دارند.",
            "صنعت گردشگری علاوه بر اینکه باعث تبادل فرهنگی بین ملت‌های مختلف می‌شود، نقش بسیار مهمی در اقتصاد کشورها ایفا می‌کند. ایجاد زیرساخت‌های مناسب، معرفی مکان‌های تاریخی و طبیعی و ارائه خدمات با کیفیت، می‌تواند توریست‌های زیادی را جذب کرده و باعث ایجاد مشاغل جدید و درآمدزایی پایدار شود.",
            "تغذیه مناسب و داشتن یک رژیم غذایی متعادل تاثیر مستقیمی بر عملکرد مغز و سیستم ایمنی بدن دارد. مصرف ویتامین‌ها، پروتئین‌های سالم و کاهش استفاده از غذاهای فرآوری شده، به بدن کمک می‌کند تا در برابر بیماری‌ها مقاوم‌تر باشد و سطح انرژی لازم برای انجام فعالیت‌های روزانه حفظ شود.",
            "کار تیمی و همکاری در محیط‌های حرفه‌ای اهمیت بسیار زیادی دارد. وقتی افراد با تخصص‌ها و دیدگاه‌های متفاوت در کنار یکدیگر روی یک پروژه کار می‌کنند، خلاقیت افزایش یافته و راه‌حل‌های بهتری برای حل مشکلات پیدا می‌شود. برای داشتن یک تیم موفق، ارتباط موثر و احترام متقابل ضروری است.",
            "سفرهای فضایی و تلاش انسان برای کشف سیارات دیگر، یکی از بلندپروازانه‌ترین پروژه‌های علمی بشریت است. ارسال کاوشگرها به مریخ و تحقیق درباره امکان حیات در خارج از کره زمین، نیازمند تکنولوژی‌های بسیار پیشرفته و همکاری‌های بین‌المللی است که مرزهای دانش فضایی را هر روز گسترده‌تر می‌کند."
        ],
        "hard": [
            "مفهوم آزادی اراده در فلسفه همواره یکی از چالش‌برانگیزترین مباحث بوده است. جبرگرایان بر این باورند که تمامی اتفاقات جهان، از جمله تصمیمات انسانی، معلول زنجیره‌ای از علت‌های پیشین هستند و در نتیجه انسان نقشی در انتخاب‌های خود ندارد. در مقابل، طرفداران اختیار استدلال می‌کنند که آگاهی و قدرت تعقل به انسان این امکان را می‌دهد که از قوانین جبر فیزیکی فراتر رفته و سرنوشت خود را آگاهانه رقم بزند. این تقابل فکری نه تنها در فلسفه، بلکه در حقوق کیفری و روانشناسی نیز تاثیرات عمیقی به جا گذاشته است.",
            "گرمایش جهانی و تغییرات اقلیمی ناشی از فعالیت‌های صنعتی، به عنوان بزرگترین تهدید زیست‌محیطی قرن حاضر شناخته می‌شود. افزایش غلظت دی‌اکسید کربن و سایر گازهای گلخانه‌ای در جو زمین، منجر به ذوب شدن یخچال‌های قطبی، بالا آمدن سطح آب دریاها و وقوع پدیده‌های جوی ویرانگر مانند طوفان‌های سهمگین و خشکسالی‌های طولانی‌مدت شده است. مقابله با این بحران نیازمند یک اراده سیاسی جهانی، گذار سریع به سمت انرژی‌های پاک و اصلاح الگوهای مصرف در سطح جوامع بشری است.",
            "مکانیک کوانتومی به عنوان یکی از ستون‌های فیزیک مدرن، درک ما از واقعیت در مقیاس‌های زیراتمی را به طور بنیادین دگرگون ساخته است. مفاهیمی چون اصل عدم قطعیت هایزنبرگ و درهم‌تنیدگی کوانتومی نشان می‌دهند که ذرات می‌توانند به طور همزمان در چندین حالت وجود داشته باشند و اندازه‌گیری یک ذره می‌تواند به صورت آنی بر وضعیت ذره‌ای دیگر در فواصل کیهانی تاثیر بگذارد. این اصول شگفت‌انگیز پایه‌گذار تکنولوژی‌های نوینی نظیر رایانش کوانتومی و رمزنگاری غیرقابل نفوذ شده‌اند.",
            "ساختار پیچیده مغز انسان و نحوه شکل‌گیری حافظه و یادگیری، همچنان یکی از بزرگترین معماهای علم عصب‌شناسی است. شبکه عظیمی از میلیاردها نورون که از طریق سیناپس‌ها با یکدیگر ارتباط برقرار می‌کنند، پایه و اساس عملکردهای شناختی، احساسات و خودآگاهی را تشکیل می‌دهند. پدیده پلاستیسیته عصبی اثبات می‌کند که مغز خاصیت انعطاف‌پذیری دارد و می‌تواند در پاسخ به تجربیات جدید، مسیرهای عصبی خود را بازسازی کند که این امر امیدهای تازه‌ای برای درمان آسیب‌های مغزی ایجاد کرده است.",
            "اقتصاد کلان به بررسی رفتار کلی سیستم‌های اقتصادی در سطح ملی و بین‌المللی می‌پردازد و متغیرهایی نظیر تورم، نرخ بیکاری و رشد تولید ناخالص داخلی را تحلیل می‌کند. سیاست‌گذاری‌های پولی و مالی که توسط بانک‌های مرکزی و دولت‌ها اعمال می‌شوند، نقش تعیین‌کننده‌ای در کنترل چرخه‌های تجاری و جلوگیری از رکود اقتصادی دارند. در دنیای به هم پیوسته امروز، بحران‌های مالی در یک منطقه می‌توانند به سرعت اثرات موجی در بازارهای جهانی ایجاد کنند که نیازمند مدیریت دقیق و همکاری‌های نهادهای پولی بین‌المللی است.",
            "معماری سیستم‌های نرم‌افزاری مقیاس‌پذیر برای پاسخگویی به نیازهای میلیون‌ها کاربر همزمان، نیازمند طراحی دقیق پایگاه‌های داده توزیع‌شده و استفاده از الگوهای میکروسرویس است. در این معماری‌ها، برنامه‌های بزرگ به سرویس‌های کوچکتر و مستقلی تقسیم می‌شوند که هر کدام وظیفه مشخصی دارند و می‌توانند به صورت مجزا توسعه یافته و مستقر شوند. این رویکرد نه تنها انعطاف‌پذیری و سرعت توسعه را افزایش می‌دهد، بلکه باعث می‌شود تا در صورت بروز خطا در یک بخش، کل سیستم از کار نیفتد و پایداری شبکه حفظ شود.",
            "تکامل زبان‌های بشری و ریشه‌یابی خانواده‌های زبانی، نشان‌دهنده تاریخ پیچیده مهاجرت‌ها و تعاملات فرهنگی انسان‌ها در طول هزاران سال است. زبان‌شناسان تاریخی با مقایسه ساختارهای دستوری و واژگان پایه‌ای در زبان‌های مختلف، توانسته‌اند درخت‌های تکاملی زبان را بازسازی کنند. این مطالعات به ما نشان می‌دهد که چگونه زبان‌ها تحت تاثیر شرایط اقلیمی، تغییرات اجتماعی و ارتباطات تجاری تغییر کرده و وام‌واژه‌هایی را از یکدیگر پذیرفته‌اند که غنای ارتباطات انسانی را به تصویر می‌کشد.",
            "در عصر دیجیتال، امنیت سایبری و حفاظت از زیرساخت‌های حیاتی اطلاعاتی به یکی از اولویت‌های اصلی امنیت ملی کشورها تبدیل شده است. حملات سازمان‌یافته توسط هکرها با هدف سرقت داده‌های حساس، باج‌گیری یا از کار انداختن شبکه‌های توزیع انرژی و سیستم‌های بانکی، می‌تواند خسارات جبران‌ناپذیری به همراه داشته باشد. استفاده از الگوریتم‌های رمزنگاری پیشرفته، فایروال‌های هوشمند و آموزش مداوم نیروی انسانی برای تشخیص حملات فیشینگ، از جمله اقدامات ضروری برای مقابله با این تهدیدات روزافزون هستند.",
            "شاهنامه فردوسی نه تنها یک حماسه ملی بی‌نظیر و شاهکار ادبی است، بلکه به عنوان سند هویت و شناسنامه تاریخی و فرهنگی ایرانیان شناخته می‌شود. فردوسی با صرف سی سال از عمر خود و با بهره‌گیری از منابع کهن، توانست اسطوره‌ها، پهلوانی‌ها و تاریخ پادشاهان باستانی را در قالب ده‌ها هزار بیت شعر حماسی به تصویر بکشد. این اثر جاودانه نقش بسیار مهمی در حفظ زبان فارسی و انتقال ارزش‌های اخلاقی نظیر میهن‌پرستی، خردورزی و مبارزه مداوم میان نیکی و بدی به نسل‌های آینده ایفا کرده است.",
            "ژنتیک مولکولی و تکنیک‌های ویرایش ژنوم مانند کریسپر، افق‌های کاملاً جدیدی را در زیست‌شناسی و پزشکی شخصی‌سازی‌شده گشوده‌اند. این ابزارهای دقیق به دانشمندان اجازه می‌دهند تا توالی‌های دی‌ان‌ای را با دقت بسیار بالایی تغییر دهند و به صورت بالقوه بیماری‌های وراثتی و ناهنجاری‌های ژنتیکی را پیش از بروز علائم، درمان کنند. با این حال، توانایی دستکاری در کد پایه حیات، بحث‌های اخلاقی گسترده‌ای را در میان دانشمندان و جوامع حقوقی درباره پیامدهای طولانی‌مدت و خطرات احتمالی این فناوری‌ها به راه انداخته است."
        ]
    }
}

def get_text_difficulty(text):
    """Returns 'easy', 'medium', or 'hard' for a given text based on length."""
    ln = len(text)
    if ln < 250:  return "easy"
    if ln < 550:  return "medium"
    return "hard"

def get_similar_text(source_text, lang, exclude):
    """Pick a text with similar difficulty to source_text."""
    diff = get_text_difficulty(source_text)
    pool = [t for t in TEXTS[lang][diff] if t != source_text and t != exclude]
    if not pool:
        pool = [t for t in TEXTS[lang][diff] if t != source_text]
    return random.choice(pool) if pool else source_text


# ─────────────────────────── MAIN GAME CLASS ──────────────────────────────────

class TypingRace(BaseGame):
    # States
    STATE_MENU      = "menu"
    STATE_READY_P1  = "ready_p1"
    STATE_TYPING_P1 = "typing_p1"
    STATE_RESULT_P1 = "result_p1"
    STATE_READY_P2  = "ready_p2"
    STATE_TYPING_P2 = "typing_p2"
    STATE_FINAL     = "final"

    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.w, self.h = screen.get_size()

        # Fonts
        try:
            self.font_lg  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 52)
            self.font_md  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 28)
            self.font_sm  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20)
            self.font_xs  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 16)
        except:
            self.font_lg  = pygame.font.SysFont("arial", 52, bold=True)
            self.font_md  = pygame.font.SysFont("arial", 28)
            self.font_sm  = pygame.font.SysFont("arial", 20)
            self.font_xs  = pygame.font.SysFont("arial", 16)

        # Colours
        self.C = {
            "bg":      (12, 12, 22),
            "panel":   (22, 22, 40),
            "accent":  (0, 230, 255),
            "green":   (0, 230, 120),
            "red":     (255, 60, 60),
            "yellow":  (255, 215, 0),
            "white":   (240, 240, 255),
            "grey":    (120, 120, 140),
            "p1":      (0, 180, 255),
            "p2":      (255, 80, 120),
        }

        self.lang     = "en"
        self.mode     = "speed"
        self.duration = 60

        self.results = {"p1": None, "p2": None}

        self.typed_text  = ""
        self.target_text = ""
        self.start_time  = 0.0
        self.error_flash = 0

        self.state = self.STATE_MENU
        self.countdown = 0
        self.countdown_start = 0

        self.cursor_on = True
        self.cursor_timer = 0

    # ──────────────── helpers ─────────────────────────────────────────────────
    def play_tick(self): pass

    def calc_wpm(self, typed, elapsed_sec):
        words = len(typed.split())
        mins  = max(elapsed_sec / 60, 0.001)
        return round(words / mins, 1)

    def calc_accuracy(self, typed, target):
        if not target: return 100.0
        correct = sum(1 for a, b in zip(typed, target) if a == b)
        return round(correct / len(target) * 100, 1)

    def pick_p1_text(self):
        pool = []
        for lvl in TEXTS[self.lang].values():
            pool.extend(lvl)
        return random.choice(pool)

    # ──────────────── state transitions ───────────────────────────────────────
    def start_countdown(self, next_state):
        self.countdown       = 3
        self.countdown_start = pygame.time.get_ticks()
        self._next_state     = next_state

    def begin_typing(self, player_key, text):
        self.current_player  = player_key
        self.typed_text      = ""
        self.target_text     = text
        self.start_time      = time.time()
        self.error_flash     = 0

    # ──────────────── events ──────────────────────────────────────────────────
    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                else:
                    self._handle_key(ev)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._handle_click(ev.pos)

    def _handle_key(self, ev):
        if self.state == self.STATE_MENU:
            pass
        elif self.state in (self.STATE_TYPING_P1, self.STATE_TYPING_P2):
            self._handle_typing_key(ev)
        elif self.state == self.STATE_RESULT_P1:
            if ev.key == pygame.K_SPACE:
                self.start_countdown(self.STATE_TYPING_P2)
                self.state = self.STATE_READY_P2
        elif self.state == self.STATE_FINAL:
            if ev.key == pygame.K_SPACE:
                self.state = self.STATE_MENU

    def _handle_typing_key(self, ev):
        mode = self.mode
        target = self.target_text

        if ev.key == pygame.K_BACKSPACE:
            return  # The error blocks advancement, no backspace needed for errors

        ch = ev.unicode
        if not ch or ord(ch) < 32:
            return

        expected_pos = len(self.typed_text)
        if expected_pos >= len(target):
            return

        # Always block incorrect character regardless of mode
        if ch == target[expected_pos]:
            self.typed_text += ch
            if len(self.typed_text) >= len(target):
                self._finish_typing()
        else:
            self.error_flash = 20
            if mode == "accuracy":
                self.typed_text = ""

    def _finish_typing(self):
        elapsed = time.time() - self.start_time
        typed   = self.typed_text
        target  = self.target_text

        wpm      = self.calc_wpm(typed, elapsed)
        accuracy = self.calc_accuracy(typed, target)

        res = {
            "wpm":      wpm,
            "accuracy": accuracy,
            "elapsed":  round(elapsed, 2),
            "typed_len": len(typed),
        }

        if self.current_player == "p1":
            self.results["p1"] = res
            self.state = self.STATE_RESULT_P1
        else:
            self.results["p2"] = res
            self._determine_winner()
            self.state = self.STATE_FINAL

    def _determine_winner(self):
        r1, r2 = self.results["p1"], self.results["p2"]
        mode = self.mode

        if mode == "accuracy":
            self.winner = "p1" if r1["elapsed"] <= r2["elapsed"] else "p2"
        elif mode == "speed":
            self.winner = "p1" if r1["wpm"] >= r2["wpm"] else "p2"
        else:
            max_wpm = max(r1["wpm"], r2["wpm"]) or 1
            s1 = 0.5 * (r1["wpm"] / max_wpm) + 0.5 * (r1["accuracy"] / 100)
            s2 = 0.5 * (r2["wpm"] / max_wpm) + 0.5 * (r2["accuracy"] / 100)
            self.winner = "p1" if s1 >= s2 else "p2"

        if self.winner == "p1":
            self.session.scores["player1"] += 1
        else:
            self.session.scores["player2"] += 1

    def _handle_click(self, pos):
        if self.state == self.STATE_MENU:
            self._menu_click(pos)
        elif self.state == self.STATE_RESULT_P1:
            if hasattr(self, "_btn_next") and self._btn_next.collidepoint(pos):
                self.start_countdown(self.STATE_TYPING_P2)
                self.state = self.STATE_READY_P2
        elif self.state == self.STATE_FINAL:
            if hasattr(self, "_btn_replay") and self._btn_replay.collidepoint(pos):
                self.state = self.STATE_MENU

    def _menu_click(self, pos):
        if hasattr(self, "_btn_lang_en") and self._btn_lang_en.collidepoint(pos):
            self.lang = "en"
        elif hasattr(self, "_btn_lang_fa") and self._btn_lang_fa.collidepoint(pos):
            self.lang = "fa"
        for m in ("accuracy", "speed", "both"):
            btn = getattr(self, f"_btn_mode_{m}", None)
            if btn and btn.collidepoint(pos):
                self.mode = m
        for d in (60, 120, 180, 300):
            btn = getattr(self, f"_btn_dur_{d}", None)
            if btn and btn.collidepoint(pos):
                self.duration = d
        if hasattr(self, "_btn_start") and self._btn_start.collidepoint(pos):
            self.results = {"p1": None, "p2": None}
            p1_text = self.pick_p1_text()
            self._p1_text = p1_text
            self._p2_text = get_similar_text(p1_text, self.lang, p1_text)
            self.start_countdown(self.STATE_TYPING_P1)
            self.state = self.STATE_READY_P1

    # ──────────────── update ──────────────────────────────────────────────────
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_timer = 0
            self.cursor_on = not self.cursor_on

        if self.error_flash > 0:
            self.error_flash -= 1

        if self.state in (self.STATE_READY_P1, self.STATE_READY_P2):
            elapsed = (pygame.time.get_ticks() - self.countdown_start) / 1000.0
            remaining = 3 - int(elapsed)
            if remaining <= 0:
                next_s = self._next_state
                if next_s == self.STATE_TYPING_P1:
                    self.begin_typing("p1", self._p1_text)
                    self.state = self.STATE_TYPING_P1
                elif next_s == self.STATE_TYPING_P2:
                    self.begin_typing("p2", self._p2_text)
                    self.state = self.STATE_TYPING_P2
            else:
                self.countdown = remaining

        if self.state in (self.STATE_TYPING_P1, self.STATE_TYPING_P2):
            if self.mode in ("speed", "both"):
                elapsed = time.time() - self.start_time
                if elapsed >= self.duration:
                    self._finish_typing()

    # ──────────────── draw helpers ─────────────────────────────────────────────
    def _draw_btn(self, rect, label, active=False, color=None):
        c = color or self.C["accent"]
        fill = c if active else self.C["panel"]
        tc   = self.C["bg"] if active else c
        pygame.draw.rect(self.screen, fill, rect, border_radius=10)
        pygame.draw.rect(self.screen, c,    rect, 2, border_radius=10)
        
        # Use render_persian_text if there are Persian characters
        if any('\u0600' <= char <= '\u06FF' for char in label):
            ts = render_persian_text(self.font_sm, label, tc)
        else:
            ts = self.font_sm.render(label, True, tc)
            
        self.screen.blit(ts, (rect.centerx - ts.get_width()//2,
                               rect.centery - ts.get_height()//2))

    def _draw_bg(self):
        self.screen.fill(self.C["bg"])
        for x in range(0, self.w, 50):
            pygame.draw.line(self.screen, (20, 20, 38), (x, 0), (x, self.h))
        for y in range(0, self.h, 50):
            pygame.draw.line(self.screen, (20, 20, 38), (0, y), (self.w, y))

    def _label(self, text, font, color, cx, y, surface=None):
        s = (surface or self.screen)
        # Use render_persian_text if there are Persian characters
        if any('\u0600' <= char <= '\u06FF' for char in text):
            ts = render_persian_text(font, text, color)
        else:
            ts = font.render(text, True, color)
            
        s.blit(ts, (cx - ts.get_width()//2, y))
        return ts.get_height()

    # ──────────────── draw states ─────────────────────────────────────────────
    def draw(self):
        self._draw_bg()

        if   self.state == self.STATE_MENU:      self._draw_menu()
        elif self.state in (self.STATE_READY_P1, self.STATE_READY_P2): self._draw_countdown()
        elif self.state in (self.STATE_TYPING_P1, self.STATE_TYPING_P2): self._draw_typing()
        elif self.state == self.STATE_RESULT_P1: self._draw_result_p1()
        elif self.state == self.STATE_FINAL:     self._draw_final()

    # ── MENU ──────────────────────────────────────────────────────────────────
    def _draw_menu(self):
        cx = self.w // 2
        self._label("⌨  TYPING RACE", self.font_lg, self.C["accent"], cx, 50)

        y = 150
        self._label("Language / زبان", self.font_md, self.C["white"], cx, y); y += 50
        self._btn_lang_en = pygame.Rect(cx - 140, y, 120, 42)
        self._btn_lang_fa = pygame.Rect(cx + 20,  y, 120, 42)
        self._draw_btn(self._btn_lang_en, "English",  self.lang == "en")
        self._draw_btn(self._btn_lang_fa, "فارسی",    self.lang == "fa")
        y += 80

        self._label("Mode / حالت", self.font_md, self.C["white"], cx, y); y += 50
        self._btn_mode_accuracy = pygame.Rect(cx - 230, y, 140, 42)
        self._btn_mode_speed    = pygame.Rect(cx - 70,  y, 140, 42)
        self._btn_mode_both     = pygame.Rect(cx + 90,  y, 140, 42)
        self._draw_btn(self._btn_mode_accuracy, "Accuracy / دقت",  self.mode == "accuracy")
        self._draw_btn(self._btn_mode_speed,    "Speed / سرعت",    self.mode == "speed")
        self._draw_btn(self._btn_mode_both,     "Both / هر دو",    self.mode == "both")
        y += 80

        if self.mode in ("speed", "both"):
            self._label("Duration / مدت (ثانیه)", self.font_md, self.C["white"], cx, y); y += 50
            labels = {60: "1 min", 120: "2 min", 180: "3 min", 300: "5 min"}
            xs = [cx - 280, cx - 90, cx + 100, cx + 110 + 90]
            for i, (d, lab) in enumerate(labels.items()):
                btn = pygame.Rect(xs[i], y, 130, 42)
                setattr(self, f"_btn_dur_{d}", btn)
                self._draw_btn(btn, lab, self.duration == d)
            y += 80
        else:
            y += 0

        expl = {
            "accuracy": "Accuracy: no mistakes allowed — first wrong key resets progress. Lowest time wins!",
            "speed":    "Speed: type as much as possible in the time limit. Most WPM wins!",
            "both":     "Both: WPM + accuracy %. Best combined score wins!",
        }
        self._label(expl[self.mode], self.font_xs, self.C["grey"], cx, y); y += 50

        self._btn_start = pygame.Rect(cx - 110, y, 220, 56)
        self._draw_btn(self._btn_start, "🚀  START", False, self.C["green"])

    # ── COUNTDOWN ─────────────────────────────────────────────────────────────
    def _draw_countdown(self):
        who = self.session.player1_name if self.state == self.STATE_READY_P1 else self.session.player2_name
        cx = self.w // 2
        self._label(f"Get Ready:  {who}", self.font_md, self.C["white"], cx, self.h//2 - 120)
        self._label(str(self.countdown), self.font_lg, self.C["yellow"], cx, self.h//2 - 50)
        self._label("Press the keys when the text appears!", self.font_sm, self.C["grey"], cx, self.h//2 + 60)

    # ── TYPING ────────────────────────────────────────────────────────────────
    def _draw_typing(self):
        cx   = self.w // 2
        pad  = 80
        mw   = self.w - 2 * pad
        target = self.target_text
        typed  = self.typed_text

        who   = self.session.player1_name if self.current_player == "p1" else self.session.player2_name
        pcol  = self.C["p1"] if self.current_player == "p1" else self.C["p2"]
        self._label(f"🎮  {who}", self.font_md, pcol, cx, 30)

        elapsed = time.time() - self.start_time
        if self.mode in ("speed", "both"):
            remaining = max(0, self.duration - elapsed)
            timer_col = self.C["red"] if remaining < 10 else self.C["yellow"]
            self._label(f"⏱  {int(remaining)}s", self.font_md, timer_col, cx, 80)
        else:
            self._label(f"⏱  {elapsed:.1f}s", self.font_md, self.C["yellow"], cx, 80)

        text_area = pygame.Rect(pad, 140, mw, self.h - 320)
        pygame.draw.rect(self.screen, self.C["panel"], text_area, border_radius=12)
        pygame.draw.rect(self.screen, (50, 50, 80), text_area, 2, border_radius=12)

        if self.error_flash > 0:
            pygame.draw.rect(self.screen, (80, 10, 10), text_area, border_radius=12)

        # Word rendering system
        words = target.split(" ")
        current_word_idx = typed.count(" ")

        space_w = self.font_md.size(" ")[0]
        line_h = self.font_md.get_height() + 10
        
        lx = text_area.right - 16 if self.lang == "fa" else text_area.x + 16
        ly = text_area.y + 16

        for i, word in enumerate(words):
            # Color logic based on current progress
            if i < current_word_idx:
                c = self.C["green"]
            elif i == current_word_idx:
                c = self.C["yellow"]
            else:
                c = self.C["grey"]

            if self.lang == "fa":
                # Persian: Right to left layout and proper shaping
                word_surf = render_persian_text(self.font_md, word, c)
                w = word_surf.get_width()
                
                if lx - w < text_area.left + 16:
                    lx = text_area.right - 16
                    ly += line_h
                    if ly > text_area.bottom - line_h:
                        break
                        
                lx -= w
                self.screen.blit(word_surf, (lx, ly))
                lx -= space_w
            else:
                # English: Left to right layout
                word_surf = self.font_md.render(word, True, c)
                w = word_surf.get_width()
                
                if lx + w > text_area.right - 16:
                    lx = text_area.x + 16
                    ly += line_h
                    if ly > text_area.bottom - line_h:
                        break
                        
                self.screen.blit(word_surf, (lx, ly))
                lx += w + space_w

        # Typing input box
        input_area = pygame.Rect(pad, self.h - 160, mw, 60)
        pygame.draw.rect(self.screen, self.C["panel"], input_area, border_radius=10)
        bc = self.C["red"] if self.error_flash > 0 else self.C["accent"]
        pygame.draw.rect(self.screen, bc, input_area, 2, border_radius=10)
        
        disp = typed[-80:] + ("|" if self.cursor_on else "")
        if self.lang == "fa":
            ts = render_persian_text(self.font_sm, disp, self.C["white"])
        else:
            ts = self.font_sm.render(disp, True, self.C["white"])
            
        self.screen.blit(ts, (input_area.x + 12, input_area.centery - ts.get_height()//2))

        # Progress bar
        if target:
            prog = len(typed) / len(target)
            bar_rect = pygame.Rect(pad, self.h - 80, mw, 18)
            pygame.draw.rect(self.screen, self.C["panel"], bar_rect, border_radius=8)
            pygame.draw.rect(self.screen, pcol,
                             (pad, self.h - 80, int(mw * prog), 18), border_radius=8)
            self._label(f"{int(prog*100)}%", self.font_xs, self.C["white"], cx, self.h - 60)

        # Live WPM
        if elapsed > 1:
            live_wpm = self.calc_wpm(typed, elapsed)
            self._label(f"WPM: {live_wpm}", self.font_sm, self.C["accent"], self.w - 120, 30)

    # ── RESULT P1 ────────────────────────────────────────────────────────────
    def _draw_result_p1(self):
        cx = self.w // 2
        r  = self.results["p1"]
        n1 = self.session.player1_name

        self._label(f"✅  {n1} — Done!", self.font_lg, self.C["p1"], cx, 80)

        y = 200
        rows = [
            ("WPM",       f"{r['wpm']}"),
            ("Accuracy",  f"{r['accuracy']}%"),
            ("Time",      f"{r['elapsed']}s"),
            ("Typed",     f"{r['typed_len']} chars"),
        ]
        for label, val in rows:
            box = pygame.Rect(cx - 260, y, 520, 52)
            pygame.draw.rect(self.screen, self.C["panel"], box, border_radius=10)
            
            ls = self._label(label, self.font_md, self.C["grey"], box.x + 80, box.centery - 14)
            vs = self.font_md.render(val, True, self.C["white"])
            self.screen.blit(vs, (box.right - vs.get_width() - 24, box.centery - vs.get_height()//2))
            y += 68

        self._label(f"Now it's {self.session.player2_name}'s turn!", self.font_sm, self.C["yellow"], cx, y + 20)

        self._btn_next = pygame.Rect(cx - 110, y + 70, 220, 52)
        self._draw_btn(self._btn_next, "▶  Next Player", False, self.C["green"])
        self._label("(SPACE)", self.font_xs, self.C["grey"], cx, y + 132)

    # ── FINAL ─────────────────────────────────────────────────────────────────
    def _draw_final(self):
        cx = self.w // 2
        r1 = self.results["p1"]
        r2 = self.results["p2"]
        n1 = self.session.player1_name
        n2 = self.session.player2_name

        winner_name  = n1 if self.winner == "p1" else n2
        winner_color = self.C["p1"] if self.winner == "p1" else self.C["p2"]

        self._label("🏆  RACE OVER!", self.font_lg, self.C["yellow"], cx, 40)
        self._label(f"Winner: {winner_name}", self.font_md, winner_color, cx, 115)

        y = 190
        headers = ["Stat", n1, n2]
        col_xs  = [cx - 260, cx - 50, cx + 120]

        for i, h in enumerate(headers):
            self._label(h, self.font_sm, self.C["accent"], col_xs[i] + 50, y)
            
        y += 36
        pygame.draw.line(self.screen, self.C["accent"], (cx - 270, y), (cx + 290, y), 1)
        y += 8

        rows = [
            ("WPM",       r1["wpm"],      r2["wpm"],      True),
            ("Accuracy",  r1["accuracy"], r2["accuracy"], True),
            ("Time (s)",  r1["elapsed"],  r2["elapsed"],  False),
            ("Typed",     r1["typed_len"],r2["typed_len"],True),
        ]
        
        for stat, v1, v2, higher_better in rows:
            box = pygame.Rect(cx - 270, y, 560, 44)
            pygame.draw.rect(self.screen, self.C["panel"], box, border_radius=8)

            self._label(stat, self.font_sm, self.C["grey"], col_xs[0] + 50, y + 10)

            def cell_col(v, other, hb):
                better = v >= other if hb else v <= other
                return self.C["green"] if better else self.C["red"]

            c1 = cell_col(v1, v2, higher_better)
            c2 = cell_col(v2, v1, higher_better)

            s1 = self.font_sm.render(str(v1), True, c1)
            s2 = self.font_sm.render(str(v2), True, c2)
            self.screen.blit(s1, (col_xs[1] + 30, y + 10))
            self.screen.blit(s2, (col_xs[2] + 30, y + 10))
            y += 52

        self._label(f"Mode: {self.mode.upper()}  |  Lang: {'English' if self.lang == 'en' else 'فارسی'}", self.font_xs, self.C["grey"], cx, y + 10)

        self._btn_replay = pygame.Rect(cx - 110, y + 50, 220, 52)
        self._draw_btn(self._btn_replay, "🔄  Play Again", False, self.C["accent"])
        self._label("(SPACE)", self.font_xs, self.C["grey"], cx, y + 112)