# Đóng gói ứng dụng từ file py thành EXE

Để đóng gói `python` thành một ứng dụng `exe` ta có thể sử dụng `auto py to exe`. Tìm hiểu thêm tại [Trang chủ](https://github.com/brentvollebregt/auto-py-to-exe).  
Cài đặt thư viện bằng cách chạy lệnh sau:  
```python
pip install auto-py-to-exe
```
Sau khi cài đặt thư viện thì tiến hành khởi chạy ứng dụng bằng câu lệnh:  
```python
auto-py-to-exe
```
Đây là giao diện của `auto-py-to-exe`  

![Giao diện auto py to exe](assets/image/auto_py_to_exe.png)

Tiếp theo ta sẽ chọn các thông tin cần thiết để cung cấp cho phần mềm:  
`Script Location`: Là tệp tin chính của chúng ta, thường sẽ là `main.py`  
`Onefile`: Nên chọn chế độ `onefile` để nó đóng gói thành 1 tệp exe  
`Console window`: Chọn `Window Based` để ẩn đi cửa sổ `console` nếu phần mềm của mình đã có giao diện  
`Icon`: Đường dẫn đến hình ảnh icon của phần mềm, lưu ý phải là file đuôi `ICO`  
`Additional File`: Thêm các file cần thiết cho phần mềm như `hình ảnh`, tệp `json`, thường là các tệp tin không thay đổi nhiều trong phần mềm.  

![Điền thông tin vào auto py to exe](assets/image/add_file_to_auto_py_to_exe.png)

## Lưu ý trong việc Additional Files

Trong chương trình này, chúng ta sử dụng các file: `data\\config.json`, `data\\log.txt `, `assets\\image\\Update_ico.ico `  

> Khi sử dụng file thì ta sử dụng đường dẫn có 2 dấu gạch chéo nha: \\  
> Không sử dụng: / hay \  

```python
json_filename = "data\\config.json"
txt_log = "data\\log.txt"
self.root.iconbitmap("assets\\image\\Update_ico.ico")

```

Khi đóng gói phần mềm bằng `pyinstall` và khởi chạy phần mềm thì chương trình của chúng ta không chạy ở thư mục chứa file `exe`, mà nó sẽ tạo ra 1 thư mục tạm có tên `_MEIxxxx` và chạy ở đấy.  

![Chạy chương trình sau khi đóng goi](assets/image/run_program_in_mei_folder.png)

Từ ảnh trên có thể thấy, thư mục chứa tệp `exe` là nằm ở `Program File (x86)` nhưng khi chạy thì thư mục thực sự đang chứa các tệp tài nguyên cần thiết cho phần mềm là `_MEI179322 nằm ở: C:\Users\Server_Quan_IT\AppData\Local\Temp\_MEI179322`  

![Thư mục MEI](assets/image/MEI_folder.png)

Vì vậy để phần mềm có thể tìm đến các tài nguyên một cách chính xác ta cần thêm hàm sau, hàm này sẽ lấy địa chỉ đang chạy của chương trình một cách chính xác, khi chạy bằng tệp python hoặc khi chạy bằng exe được đóng gói bằng pyinstall:  

```python
def resource_path(relative_path):
    """ Trả về đường dẫn đến file tài nguyên khi đóng gói với PyInstaller """
    try:
        # Khi chạy ứng dụng từ file .exe
        base_path = sys._MEIPASS
    except Exception:
        # Khi chạy từ mã nguồn Python
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
```
Sau đó ta thay thế các đoạn mã sử dụng tài nguyên bằng cách sử dụng hàm `resource_path` như sau:  

```python
json_filename = resource_path("data\\config.json")
txt_log = resource_path("data\\log.txt")
self.root.iconbitmap(resource_path("assets\\image\\Update_ico.ico"))
```
Và cách thêm các tài nguyên để đóng gói vào `auto-py-to-exe` như sau:

![Thêm file ](assets/image/add_file_to_au_to_py_to_exe.png)

Chương trình của tôi dùng 3 file, và 3 file đó có đường dẫn như sau: `data\\my_file1`, `data\\my_file2`, `assets\\image\\my_file3`  
Vì vậy khi ta chọn chức năng `Add Folder` thì ta sẽ chọn folder chứa các tài nguyên của chúng ta là `data`, và `image` thì nó sẽ tự động lấy hết các tệp tin bên trong thư mục đó (vì vậy chỉ bỏ vào các tệp tin cần thiết, nếu không nó sẽ copy hết các file và gây ra dư thừa và nặng chương trình sau khi đóng gói) và ô kế bên đó phải điền đúng đường dẫn khi ta sử dụng, nếu không sẽ lỗi. Vì vậy ta sẽ điền tương ứng là `assets/image/` và `data/` nó sẽ tự tạo 2 thư mục đó và đưa các file cần thiết vào đúng 2 thư mục đó.  

### Mình sẽ không additional file data vào, vì chương trình của mình có địa chỉ api không cố định, nó sẽ thay đổi thường xuyên nên cần để file này nằm ở thư mục bên ngoài, để dễ dàng thay đổi. Mình làm theo cách 0 ở mục lưu ý, hoặc import json mẫu để xem chi tiết.  

`Advance`: Thường đây sẽ là nơi nhập tên của phần mềm và các thư viện mà đã sử dụng bằng `hidden-import`  

![Nhập tên và thư viện](assets/image/advance_auto_py_to_exe.png)

`Setting`: Chủ yếu dùng để xuất file json hoặc nhập file json cho các lần sau sử dụng lại, không cần điền lại các thông số từ đầu.  

![Nhập hoặc xuát file json để lưu quá trình cấu hình](assets/image/setting_auto_py_to_exe.png)

Sau khi cấu hình hoàn tất thì chọn `Export Config to JSON File` để lưu file này lại cho các lần sử dụng sau.  

Sau đó `import` tệp json đã được chuẩn bị sẵn [tại đây](data/auto-py-to-exe-updater.json). **Lưu ý đường dẫn đến các tệp tin hình ảnh, json đang không khớp, thay đổi cho phù hợp với thực tế**.  

![Import tệp json vào phần mềm auto py to exe](assets/image/json_exe_use_auto_py_to_exe.png)

Sau khi hoàn thành thì vào thư mục `output` tương ứng sẽ thấy một tệp exe, chỉ cần chạy tệp này là được, Nếu chương trình của bạn có các thư mục thay đổi hằng ngày thì có thể bỏ nó vào vị trí tương ứng với vị trí đặt phần mềm.  

![Hoàn thành chuyển đổi py thành exe](assets/image/success.png)

# Một số lưu ý:  

## 0. Không thêm tệp vào exe
Có một số trường hợp ta không nên sử dụng `Additional Files`:  
Chúng ta có 1 tệp `json` chứa các thiết lập ban đầu như `địa chỉ api`, `tệp ngôn ngữ`, ... đây là những thông số có thể thay đổi thường xuyên, vì vậy ta không thêm nó trực tiếp vào exe, mà để nó ở cùng thư mục chứa tệp thực thi `exe` để nó dễ dàng truy cập và ta cũng dễ dàng chỉnh sửa tệp này.  
Khi đó ta sẽ không sử dụng hàm `resource_path` để đọc tệp tin mà sẽ đọc trực tiếp, còn các file khác mà cần thì vẫn đọc bằng `resource_path` như bình thường và `phải thêm vào additon file`:  

```python
json_filename = "data\\config.json"
txt_log = "data\\log.txt"
self.root.iconbitmap("assets\\image\\Update_ico.ico")
```
Sau khi có file exe thì ta copy 2 thư mục này vào cùng vị trí với exe. Để nó có thể tìm được các tệp này.  

![Thêm file thủ công](assets/image/not_use_add_file.png)

## 1. Lỗi không tìm thấy thư viện
Khi chuyển đổi file `python` thành `exe` sẽ gặp lỗi như `ModuleNotFound: No module named 'xxx'`  

![Lỗi thiếu thư viện](assets/image/modul_not_found.png)

Ta có thể thấy rằng nó đang báo thiếu thư viện `xxx`.  
Nếu thư viện `xxx` của bạn được cài đặt bằng `pip` thì sử dụng `--hidden-import` để thêm thư viện đó. Ví dụ như `cv2`, `PIL`, `PIL.Image`, ...  

![alt text](assets/image/hidden_import_library.png)

Còn nếu bạn tạo các `tệp py` và xem nó như một module và import nó như ví dụ dưới đây:  

![alt text](assets/image/py_module.png)

Ta có thể thấy các hàm được import vào thông qua các thư mục và file py. Tôi có cấu trúc thư mục như sau:  

![alt text](assets/image/tree_folder.png)

Ta chỉ cần thêm tệp tin `__init__.py` thì khi đóng gói nó sẽ tự động tìm kiếm các module này và thêm vào. Và lưu ý:  

> Thư mục gốc không có tệp tin __init__.py, chỉ có những thư mục nòa chứa tệp tin mà được import thì mới có  
> Như ảnh trên thì thư mục gốc (thư mục chứa tệp main.py) đang có tệp tin __init__.py, ta cần xóa bỏ nó trước khi chạy đóng gói  


## 2. Lỗi nhận diện nhầm virus
`Window defender` có thể nhận nhầm đây là 1 phần mềm có chứa `virus` nên khi tạo thành file exe thì ngay lập tức bị xóa, vì vậy khi nó hiển thị thông báo phát hiện virus thì nhanh chóng ấn vào đó và cho phép nó chạy, thì file exe sẽ không bị xóa.  

## Một số lỗi khác 

Xem thêm một số lỗi khác tại [trang chủ](https://nitratine.net/blog/post/issues-when-using-auto-py-to-exe/#debugging)