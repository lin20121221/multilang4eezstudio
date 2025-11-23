# multilang4eezstudio
Multilanguage tool for LVGL project of EEZ studio


Usage:  
1. Place both the `multi_lang.txt` and `multilang.py` files into the target folder of your EEZ Studio LVGL project, for example: `src\ui`.  
2. Edit the `multi_lang.txt` file to add all necessary phrases, terms, and paragraphs in various languages. Use spaces or tabs to separate different languages in `multi_lang.txt`. If the content contains spaces or tabs, enclose it in double quotes. The last column in `multi_lang.txt` represents the array name, which will be used in the generated `strings.h` file by the tool.  
3. After editing, run the following command in the terminal:  
   python multilang.py <c_source_file>
4. Include the tool-generated `strings.h` file in the project.


用法：
1. 将multi_lang.txt和multilang.py文件一同放入EEZ studio的LVGL项目目标文件夹内，例如：src\ui。
2. 编辑文件multi_lang.txt，添加所有需要的各种语言词组，短语和段落。multi_lang.txt中用空格或tab区分各语言，所以包含空格或tab的内容需要包含在双引号内。multi_lang.txt中最后一列为数组名称，用于工具生成的strings.h中。
3. 编辑完成后，在命令行运行：
    python multilang.py <c_source_file>
4. 在项目中引用工具生成的 strings.h 文件
5. 
