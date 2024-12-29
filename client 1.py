import socket
import tkinter as tk
from tkinter import filedialog, messagebox
import logging
import os
import threading
from tkinter import ttk  # Thêm để sử dụng Progressbar

# Cấu hình logging
logging.basicConfig(
    filename="client_log.txt",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class FileClientApp:
    def __init__(self, master):
        self.master = master
        self.master.title("File Sharing Client")
        self.master.geometry("700x600")  # Tăng kích thước để chứa Progressbar và biểu đồ

        self.server_ip = "127.0.0.1"  # Server IP
        self.server_port = 9999       # Server Port

        self.client_socket = None
        self.selected_file = None  # Biến để lưu tên file được chọn

        # Giao diện người dùng
        self.status_label = tk.Label(master, text="Status: Disconnected", fg="red", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.connect_button = tk.Button(master, text="Connect to Server", command=self.connect_to_server, width=20)
        self.connect_button.pack(pady=5)

        self.disconnect_button = tk.Button(master, text="Disconnect", command=self.disconnect_from_server, state=tk.DISABLED, width=20)
        self.disconnect_button.pack(pady=5)

        self.upload_button = tk.Button(master, text="Upload File", command=self.upload_file, state=tk.DISABLED, width=20)
        self.upload_button.pack(pady=5)

        self.list_button = tk.Button(master, text="List Files on Server", command=self.list_files, state=tk.DISABLED, width=20)
        self.list_button.pack(pady=5)

        self.file_listbox = tk.Listbox(master, width=60, height=15, state=tk.DISABLED)
        self.file_listbox.pack(pady=10)
        # Bind cả double-click và single-click để đảm bảo chọn file
        self.file_listbox.bind('<Double-1>', self.select_file)
        self.file_listbox.bind('<ButtonRelease-1>', self.select_file)

        self.download_button = tk.Button(master, text="Download Selected File", command=self.download_file, state=tk.DISABLED, width=25)
        self.download_button.pack(pady=5)

        # Thêm Progress Bars
        self.upload_progress = ttk.Progressbar(master, orient='horizontal', length=600, mode='determinate')
        self.upload_progress.pack(pady=5)

        self.download_progress = ttk.Progressbar(master, orient='horizontal', length=600, mode='determinate')
        self.download_progress.pack(pady=5)

        # Đăng ký phương thức đóng ứng dụng
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def connect_to_server(self):
        if self.client_socket:
            messagebox.showinfo("Info", "Already connected to the server.")
            return
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            self.status_label.config(text="Status: Connected", fg="green")
            self.upload_button.config(state=tk.NORMAL)
            self.list_button.config(state=tk.NORMAL)
            self.disconnect_button.config(state=tk.NORMAL)
            self.connect_button.config(state=tk.DISABLED)
            logging.info(f"Connected to server at {self.server_ip}:{self.server_port}")
            # self.update_graphs()  # Nếu Bạn Có Chức Năng Vẽ Biểu Đồ
        except Exception as e:
            logging.error(f"Failed to connect to server: {e}")
            messagebox.showerror("Error", f"Failed to connect to server: {e}")
            self.client_socket = None

    def disconnect_from_server(self):
        if self.client_socket:
            try:
                self.client_socket.close()
                self.client_socket = None
                self.status_label.config(text="Status: Disconnected", fg="red")
                self.upload_button.config(state=tk.DISABLED)
                self.list_button.config(state=tk.DISABLED)
                self.download_button.config(state=tk.DISABLED)
                self.file_listbox.config(state=tk.DISABLED)
                self.disconnect_button.config(state=tk.DISABLED)
                self.connect_button.config(state=tk.NORMAL)
                self.selected_file = None  # Reset selected file
                self.upload_progress['value'] = 0
                self.download_progress['value'] = 0
                logging.info("Disconnected from server.")
                messagebox.showinfo("Disconnected", "You have been disconnected from the server.")
            except Exception as e:
                logging.error(f"Error disconnecting from server: {e}")
                messagebox.showerror("Error", f"Failed to disconnect from server: {e}")

    def upload_file(self):
        if not self.is_connected():
            messagebox.showerror("Error", "Not connected to the server.")
            return
        threading.Thread(target=self._upload_file, daemon=True).start()

    def _upload_file(self):
        try:
            file_path = filedialog.askopenfilename()
            if not file_path:
                return

            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            logging.info(f"Starting upload for file: {file_name} with size: {file_size} bytes")

            # Reset Progress Bar
            self.upload_progress['value'] = 0
            self.upload_progress['maximum'] = file_size

            # Gửi lệnh UPLOAD với định dạng đúng (UPLOAD filename filesize)
            upload_command = f"UPLOAD {file_name} {file_size}\n"  # Thêm '\n' nếu server mong đợi
            self.client_socket.sendall(upload_command.encode('utf-8'))

            with open(file_path, "rb") as f:
                total_bytes_sent = 0
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    self.client_socket.sendall(chunk)
                    total_bytes_sent += len(chunk)
                    self.upload_progress['value'] = total_bytes_sent
                    self.master.update_idletasks()

            logging.info(f"File '{file_name}' uploaded successfully. Total bytes sent: {total_bytes_sent}")

            # Nhận phản hồi từ server
            response = self.recv_line().strip()
            logging.info(f"Received response: {response} for file: {file_name}")

            if response == "UPLOAD_SUCCESS":
                logging.info(f"Server confirmed upload success for file: {file_name}")
                messagebox.showinfo("Success", f"File '{file_name}' uploaded successfully.")
            else:
                logging.warning(f"Server response: {response} for file: {file_name}")
                messagebox.showerror("Error", f"Failed to upload file. Server response: {response}")

            # Kiểm tra xem tất cả byte đã được gửi thành công
            if total_bytes_sent != file_size:
                logging.warning(f"Mismatch in file size. Sent: {total_bytes_sent}, Expected: {file_size}")
                messagebox.showwarning("Warning", "Mismatch in file size. Upload may be incomplete.")

            # Reset Progress Bar sau khi hoàn thành
            self.upload_progress['value'] = 0

        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            messagebox.showerror("Error", f"Failed to upload file: {e}")
            self.upload_progress['value'] = 0

    def list_files(self):
        if not self.is_connected():
            messagebox.showerror("Error", "Not connected to the server.")
            return
        threading.Thread(target=self._list_files, daemon=True).start()

    def _list_files(self):
        try:
            self.client_socket.sendall(b"LIST\n")  # Thêm '\n' nếu server mong đợi
            logging.info("Requesting file list from server")
            file_list = self.client_socket.recv(4096).decode("utf-8")
            files = [f.strip() for f in file_list.split("|") if f.strip()]  # Loại bỏ chuỗi rỗng và khoảng trắng

            self.file_listbox.config(state=tk.NORMAL)
            self.file_listbox.delete(0, tk.END)
            for file in files:
                self.file_listbox.insert(tk.END, file)
            self.file_listbox.config(state=tk.NORMAL)  # Cho phép tương tác

            self.selected_file = None  # Reset khi danh sách file được cập nhật

            if files:
                logging.info(f"Received file list: {files}")
                self.download_button.config(state=tk.DISABLED)  # Chưa có file nào được chọn
            else:
                logging.info("No files found on the server.")
                self.download_button.config(state=tk.DISABLED)
                messagebox.showinfo("Info", "No files found on the server.")
        except Exception as e:
            logging.error(f"Error listing files: {e}")
            messagebox.showerror("Error", f"Failed to list files: {e}")

    def select_file(self, event):
        logging.info("select_file method called.")
        selection = self.file_listbox.curselection()
        if not selection:
            logging.info("No selection made.")
            return
        selected_file = self.file_listbox.get(selection[0])
        self.selected_file = selected_file  # Lưu tên file được chọn
        logging.info(f"File selected: {selected_file}")
        # messagebox.showinfo("File Selected", f"Selected File: {selected_file}")
        self.download_button.config(state=tk.NORMAL)  # Bật nút Download khi file được chọn

    def download_file(self):
        logging.info("Download button clicked.")
        if not self.is_connected():
            messagebox.showerror("Error", "Not connected to the server.")
            logging.warning("Download attempted without connection.")
            return
        if not self.selected_file:
            messagebox.showerror("Error", "No file selected.")
            logging.warning("Download attempted without selecting a file.")
            return
        threading.Thread(target=self._download_file, daemon=True).start()

    def _download_file(self):
        try:
            file_name = self.selected_file
            logging.info(f"Requesting download for file: {file_name}")
            self.client_socket.sendall(f"DOWNLOAD {file_name}\n".encode())  # Thêm '\n' nếu server mong đợi

            # Đọc phản hồi dòng từ server
            response = self.recv_line().strip()
            logging.info(f"Received response: {response}")

            if response.startswith("FILE_FOUND"):
                parts = response.split()
                if len(parts) != 2:
                    logging.error(f"Invalid FILE_FOUND response format: {response}")
                    messagebox.showerror("Error", "Invalid response from server.")
                    return
                _, filesize_str = parts
                try:
                    filesize = int(filesize_str)
                except ValueError:
                    logging.error(f"Invalid filesize in response: {filesize_str}")
                    messagebox.showerror("Error", "Invalid filesize received from server.")
                    return

                save_path = filedialog.asksaveasfilename(
                    defaultextension="", initialfile=file_name
                )
                if not save_path:
                    logging.warning(f"Download cancelled for file: {file_name}")
                    return

                # Thiết lập Progress Bar
                self.download_progress['value'] = 0
                self.download_progress['maximum'] = filesize

                total_bytes = 0
                with open(save_path, "wb") as f:
                    while total_bytes < filesize:
                        data = self.client_socket.recv(min(4096, filesize - total_bytes))
                        if not data:
                            break
                        f.write(data)
                        total_bytes += len(data)
                        self.download_progress['value'] = total_bytes
                        self.master.update_idletasks()

                if total_bytes == filesize:
                    logging.info(f"File '{file_name}' downloaded successfully. Total bytes: {total_bytes}")
                    messagebox.showinfo("Success", f"File '{file_name}' downloaded successfully.")
                else:
                    logging.warning(f"Incomplete download for file '{file_name}'. Expected {filesize}, got {total_bytes}.")
                    messagebox.showerror("Error", f"Incomplete download for file '{file_name}'.")

                # Reset Progress Bar sau khi hoàn thành
                self.download_progress['value'] = 0

            elif response == "FILE_NOT_FOUND":
                logging.error(f"File '{file_name}' not found on server.")
                messagebox.showerror("Error", f"File '{file_name}' not found on server.")
            else:
                logging.error(f"Unexpected response during download: {response}")
                messagebox.showerror("Error", "Unexpected error during download.")
        except Exception as e:
            logging.error(f"Error during download: {e}")
            messagebox.showerror("Error", f"Failed to download file: {e}")

        # Reset selected_file sau khi download
        self.selected_file = None
        self.download_button.config(state=tk.DISABLED)

    def recv_line(self):
        line = ""
        while True:
            try:
                char = self.client_socket.recv(1).decode('utf-8')
                if not char:
                    break
                if char == '\n':
                    break
                line += char
            except Exception as e:
                logging.error(f"Error receiving line: {e}")
                break
        return line

    def is_connected(self):
        return self.client_socket is not None

    def on_closing(self):
        self.disconnect_from_server()
        self.master.destroy()


def main():
    root = tk.Tk()
    app = FileClientApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
