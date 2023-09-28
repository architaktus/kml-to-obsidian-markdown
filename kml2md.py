
from pykml import parser
import os
import re
import shutil

current_directory = os.getcwd() # 获取当前工作目录
target_extension = ".kml"  # 查找所有 .kml 文件
# 获取当前工作路径下所有kml后缀的文件名和文件路径
matching_files = [(os.path.splitext(file)[0], os.path.join(current_directory, file)) for file in os.listdir(current_directory) if file.endswith(target_extension)]

for file_name, file_path in matching_files:
    print("文件名:", file_name)
    print("文件路径:", file_path)

    # Create folder for each kml file
    kml_folder_path = file_name
    if not os.path.exists(kml_folder_path):    
        os.mkdir(kml_folder_path)
        print(f"Folder '{kml_folder_path}' created successfully.\n")
    else:
        print(f"Folder '{kml_folder_path}' already exists.")

    outputlog_name = f'Log_{file_name}.txt'
    outputlog_path = os.path.join(kml_folder_path,outputlog_name)

    with open(outputlog_path, 'w', encoding='utf-8') as file0: 
        # parse kml file
        with open(file_path, 'r', encoding='utf-8') as f:
            kml_doc = parser.parse(f).getroot()
            print(f'成功读取{kml_doc}\n')
            file0.write(f'从{file_path}创建的文件如下：\n\n')          

        # 准备一个函数来清理文件夹名称 //////////////////////////////////////////函数clean_name
        def clean_name(name):
            # 替换特殊字符
            name = name.replace('?', '_')  # 将 ? 替换为 _
            name = name.replace('/', '-')  # 将 / 替换为 -    
            name = name.replace('"', '_')  # 将 " 替换为 _
            name = name.replace(':', '_')  # 将 : 替换为 _
            cleaned_name = name    
            return cleaned_name
        
        # 查找 <img>/<href> 标签 //////////////////////////////////////////函数img_src
        def img_src(md_descrip,is_href = False):
            img_path = []  
            img_tags = []
            if is_href is True:
                img_path.append(f'"{md_descrip}"') #直接作为文件路径
            else:
                if md_descrip:
                    img_tags = re.findall(r'<img [^>]*>', md_descrip)
                    if img_tags is not None:
                        for tags in img_tags:
                            img_src_match = re.search(r'src="([^"]+)"', tags) 
                            # 提取匹配到的 src 属性值作为文件路径
                            img_path.append(f'"{img_src_match.group(1)}"')
            return img_path


        def md_desc(placemark, folder_path, indent):
            md_text = None
            md_text_origin = ''
            img_path_origin = None
            if hasattr(placemark, 'description') and placemark.description is not None:
                md_text_origin = placemark.description.text
                img_path_origin = img_src(md_text_origin) # 查找img，写入列表
            if hasattr(placemark, 'Icon'):
                if hasattr(placemark.Icon, 'href') and placemark.Icon.href is not None:
                    md_text_link_origin = placemark.Icon.href.text                         
                    is_href = True                    
                    img_path_origin = img_src(md_text_link_origin, is_href) # 查找img，写入列表            
            
            md_text = md_text_origin

            if img_path_origin:
                print(f"         /////log.Attachment {placemark.name.text}: {img_path_origin}")  # //////////////////Log
                # 创建附件文件夹
                att_path = os.path.join(folder_path, f"_attachments")
                if not os.path.exists(att_path):    
                    os.mkdir(att_path)               
                
                photoheader = "\n# 图片\n"
                md_text += photoheader
                img_count = 0

                for item in img_path_origin:
                    md_text += f"\n原链接：{item}\n"
                    img_name = re.search(r'[^/\\]*$', item.strip('"')).group() # 提取文件名
                    while os.path.exists(os.path.join(att_path, img_name)): # 检查同名
                        source_name, source_extension = os.path.splitext(img_name)  # 拆分文件名和扩展名
                        img_name = f"{source_name}_new{source_extension}"  # 加扩展名
                    att_path_old = item.strip('"')
                    print(f'        /////log.Att.path.new {os.path.join(att_path, img_name)}')    # //////////////////Log
                    print(f"        /////log.Att.path.old {att_path_old}") # //////////////////Log
                    shutil.copy2(att_path_old, os.path.join(att_path, img_name)) # 复制图片

                    md_text_img = f"![[{img_name}]]\n"                    
                    md_text = md_text + md_text_img

                    img_count += 1
                    file0.write(f"{indent}    Photo{img_count}. {img_name}\n")
            return md_text

        def write_md_n_log(folder, indent='', parent_path='', current_index = None, index=None):  # //////////////////////////////////////////函数write_md_n_log     
            folder_name_temp = folder.name.text if hasattr(folder, 'name') and folder.name is not None else ''
            folder_name = clean_name(folder_name_temp)
            
            # 创建文件夹
            if parent_path:
                folder_path = os.path.join(parent_path, folder_name)                
            else:
                folder_path = os.path.join(kml_folder_path, folder_name)
            os.mkdir(folder_path)
            print(f"Folder '{folder_name}' created successfully.\n")               

            folder_index= f"{current_index}" if current_index is not None else str(index)
            folder_name_with_index = f"{folder_index} {folder_name}"
            file0.write(f"{indent}Folder {folder_name_with_index}\n") #写入log

            #为每个文件夹创建一个md
            md_path = os.path.join(folder_path, f"{folder_name}.md")
            with open(md_path, "w", encoding="utf-8") as foldermd: 
                foldermd_frontmatter = "---\nalias:\n---\n"
                foldermd.write(foldermd_frontmatter)

                #将文件夹的描述加入其中
                if hasattr(folder, 'description'): 
                    md_text = folder.description.text
                    foldermd.write(f"文件夹描述：{md_text}\n")  #写入md
                file0.write(f'{indent}  md for folder "{folder_name}"\n\n')
            
                #遍历Placemark，写入
                if hasattr(folder, 'Placemark'):
                    foldermd.write(f'# Placemark\n')
                    for placemark in folder.Placemark:
                        md_name_origin = placemark.name.text if hasattr(placemark, 'name') and placemark.name is not None else ''
                        md_name = clean_name(md_name_origin)
                        md_path = os.path.join(folder_path, f"{md_name}.md")
                        md_text = ''

                        # geolocation表达式
                        coords = placemark.Point.coordinates.text.strip()
                        co_pattern = r'(\d+\.\d+),(\d+\.\d+),(.*)'
                        coords_Lat = re.sub(co_pattern, r'\2', coords)
                        coords_Lon = re.sub(co_pattern, r'\1', coords)
                        co_md = f"---\nlocation:\n  - {coords_Lat}\n  - {coords_Lon}\n---\n" #写入md frontmatter     

                        file0.write(f"{indent}  {md_name}\n")
                        md_text = md_desc(placemark, folder_path, indent) #description相关

                        with open(md_path, "w", encoding="utf-8") as file:              
                            file.write(f"{co_md}")
                            file.write(f"原标题：{md_name_origin}\n")
                            if md_text is not None:
                                file.write(f"{md_text}")  #description写入md
                        file0.write(f'{indent}    Placemark --> md "{md_name}" 写入成功\n\n')
                        foldermd.write(f'[[{md_name}]]\n')
                        

                if hasattr(folder, 'GroundOverlay'):
                    foldermd.write(f'# GroundOverlay\n')
                    for GroundOverlay in folder.GroundOverlay:
                        md_name_origin = GroundOverlay.name.text if hasattr(GroundOverlay, 'name') and GroundOverlay.name is not None else ''
                        md_name = clean_name(md_name_origin)
                        md_path = os.path.join(folder_path, f"{md_name}.md")
                        md_text = ''

                        # geolocation表达式
                        north = float(GroundOverlay.LatLonBox.north.text)
                        south = float(GroundOverlay.LatLonBox.south.text)
                        east = float(GroundOverlay.LatLonBox.east.text)
                        west = float(GroundOverlay.LatLonBox.west.text)
                        coords_Lat = (north + south) / 2
                        coords_Lon = (east + west) / 2
                        co_md = f"---\nlocation:\n  - {coords_Lat}\n  - {coords_Lon}\n---\n" #写入md frontmatter

                        file0.write(f"{indent}  {md_name}\n")
                        md_text = md_desc(GroundOverlay, folder_path, indent) #description相关

                        with open(md_path, "w", encoding="utf-8") as file:              
                            file.write(f"{co_md}")
                            file.write(f"原标题：{md_name_origin}\n")
                            file.write(f"{md_text}")  #description写入md
                        file0.write(f'{indent}    GroundOverlay --> md "{md_name}" 写入成功\n\n')
                        foldermd.write(f'[[{md_name}]]\n')
                
            
            # 递归处理子文件夹
            if hasattr(folder, 'Folder'):
                for index, subfolder in enumerate(folder.Folder, start=1):
                    subfolder_index = f"{folder_index}-{index}"
                    write_md_n_log(subfolder, indent + '  ', folder_path, subfolder_index, index)

        # 调用写入函数并传入根文件夹
        for index, folder in enumerate(kml_doc.Document.Folder, start = 1):
            write_md_n_log(folder, index = index)