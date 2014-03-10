## Monkeyrunner Sites Verificator ##
Sites verificator allows you to prepare snapshot samples of web pages in browser and to perform automatic checks, to make sure they weren't broken.

Project consist of verificator itself and test browser.

To run project download _verificator_ folder, set correct path to image-magick in `config.py` and modify saple list of URLs in assets folder launch `monkeyrunner test.py init` to prepare samples and `monkeyrunner test.py` to compare current site state with given samples.
*Assets* folder already contains sample URL and test borwser, so it's ready to launch. To check multiple URLs just put them all into same file line by line.
*Results* folder already contains sample output file in jUnit XML format, so it can be imported to any apllication that supports it (Eclipse for example)


*Test-browser* is the android sample browser project that always loads new page in place of old one and never asks to access location to provide more prodictable and reliable test lauch results. You don't have to build it yourself, precompiled binary already included into assets folder and will installed automatically.
