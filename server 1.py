import socket
import threading
import os
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FileServerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("File Sharing Server")
        self.master.geometry("1200x800")  # Tăng kích thước để chứa nhiều biểu đồ

        self.server_socket = None
        self.running = False
        self.received_files_path = "received_files"
        self.log_file = "transfer_log.csv"
        os.makedirs(self.received_files_path, exist_ok=True)

        # Khởi tạo tệp log với các cột bao gồm 'Latency'
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("Filename,FileSize,Duration,Status,Latency\n")  # Thêm cột Latency

        # Bộ đếm cho các chỉ số hiệu suất
        self.total_transfers = 0
        self.failed_transfers = 0

        # Nhãn Trạng Thái Server
        self.status_label = tk.Label(master, text="Server Status: Stopped", fg="red", font=("Arial", 14))
        self.status_label.pack(pady=10)

        # Khung Nút Điều Khiển
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(pady=5)

        self.start_button = tk.Button(
            self.control_frame,
            text="Start Server",
            command=self.start_server,
            width=15,
            font=("Arial", 12)
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(
            self.control_frame,
            text="Stop Server",
            command=self.stop_server,
            state=tk.DISABLED,
            width=15,
            font=("Arial", 12)
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # Khung Thông Tin để chứa Received Files và Server Log
        self.info_frame = tk.Frame(master)
        self.info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Phần Received Files
        self.files_frame = tk.Frame(self.info_frame)
        self.files_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        self.files_label = tk.Label(self.files_frame, text="Received Files:", font=("Arial", 12, "bold"))
        self.files_label.pack(pady=5)

        self.files_listbox = tk.Listbox(self.files_frame, width=50, height=20, font=("Arial", 10))
        self.files_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.files_listbox.bind('<Double-1>', self.open_file)

        self.delete_button = tk.Button(
            self.files_frame,
            text="Delete File",
            command=self.delete_file,
            width=20,
            font=("Arial", 12)
        )
        self.delete_button.pack(pady=10)

        # Phần Server Log
        self.log_frame = tk.Frame(self.info_frame)
        self.log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        self.log_label = tk.Label(self.log_frame, text="Server Log:", font=("Arial", 12, "bold"))
        self.log_label.pack(pady=5)

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            width=60,
            height=20,
            state=tk.DISABLED,
            font=("Arial", 10)
        )
        self.log_text.pack(pady=5, fill=tk.BOTH, expand=True)

        # Khung Chỉ Số Hiệu Suất
        self.performance_frame = tk.Frame(master)
        self.performance_frame.pack(pady=10)

        self.transfer_speed_label = tk.Label(
            self.performance_frame,
            text="Transfer Performance: N/A",
            fg="blue",
            font=("Arial", 12)
        )
        self.transfer_speed_label.pack(side=tk.LEFT, padx=20)

        self.packet_loss_label = tk.Label(
            self.performance_frame,
            text="Packet Loss Rate: N/A",
            fg="orange",
            font=("Arial", 12)
        )
        self.packet_loss_label.pack(side=tk.LEFT, padx=20)

        # Khung Biểu Đồ
        self.graph_frame = tk.Frame(master)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Khởi tạo biểu đồ
        self.update_graphs()

        # Optional: Bắt đầu cập nhật biểu đồ định kỳ
        # self.start_graph_refresh()

    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def start_server(self):
        if not self.running:
            try:
                self.running = True
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind(("0.0.0.0", 9999))
                self.server_socket.listen(5)
                self.status_label.config(text="Server Status: Running", fg="green")
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                threading.Thread(target=self.accept_clients, daemon=True).start()
                self.log_message("Server started on port 9999.")
            except Exception as e:
                self.log_message(f"Failed to start server: {e}")
                self.running = False
                self.status_label.config(text="Server Status: Stopped", fg="red")
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)

    def stop_server(self):
        if self.running:
            self.running = False
            try:
                self.server_socket.close()
                self.status_label.config(text="Server Status: Stopped", fg="red")
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.log_message("Server stopped.")
            except Exception as e:
                self.log_message(f"Error stopping server: {e}")

    def accept_clients(self):
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, client_address), daemon=True).start()
                self.log_message(f"Client connected: {client_address}")
            except OSError:
                break  # Socket đã được đóng
            except Exception as e:
                self.log_message(f"Error accepting client: {e}")

    def handle_client(self, client_socket, client_address):
        try:
            while self.running:
                request = client_socket.recv(1024).decode(errors="surrogateescape")
                if not request:
                    break

                if request.startswith("UPLOAD"):
                    self.handle_upload(client_socket, request)
                elif request.startswith("LIST"):
                    self.handle_list(client_socket)
                elif request.startswith("DOWNLOAD"):
                    self.handle_download(client_socket, request, client_address)
                elif request.startswith("DELETE"):
                    self.handle_delete(client_socket, request)
                else:
                    client_socket.sendall(b"ERROR: Unknown command.")
        except Exception as e:
            self.log_message(f"Error handling client {client_address}: {e}")
            self.failed_transfers += 1
            self.update_packet_loss_rate()
        finally:
            client_socket.close()
            self.log_message(f"Client disconnected: {client_address}")

    def handle_upload(self, client_socket, request):
        try:
            # Log yêu cầu nhận
            self.log_message(f"Received UPLOAD command: {request}")
            
            # Tách các phần của yêu cầu thành 3 phần
            parts = request.strip().split(" ", 2)  # Chia thành 3 phần: "UPLOAD", "filename", "filesize"
            if len(parts) < 3:
                client_socket.sendall(b"ERROR: Invalid UPLOAD command. Format should be: UPLOAD filename filesize")
                self.failed_transfers += 1
                self.update_packet_loss_rate()
                self.log_message(f"Invalid UPLOAD command received: {request}")
                return

            _, filename, filesize_str = parts

            # Xác minh và chuyển đổi filesize thành integer
            try:
                filesize = int(filesize_str)
            except ValueError:
                client_socket.sendall(b"ERROR: Filesize must be an integer.")
                self.failed_transfers += 1
                self.update_packet_loss_rate()
                self.log_message(f"Invalid filesize received for file '{filename}': '{filesize_str}'")
                return

            # Đảm bảo tên file an toàn
            safe_filename = os.path.basename(filename)
            filepath = os.path.join(self.received_files_path, safe_filename)

            # Ghi nhận thời gian bắt đầu
            start_time = time.time()
            total_bytes = 0

            with open(filepath, "wb") as f:
                while total_bytes < filesize:
                    data = client_socket.recv(min(4096, filesize - total_bytes))
                    if not data:
                        break
                    f.write(data)
                    total_bytes += len(data)

            # Ghi nhận thời gian kết thúc
            end_time = time.time()
            duration = end_time - start_time  # Duration tính bằng giây
            transfer_speed = total_bytes / duration if duration > 0 else 0
            latency = duration * 1000  # Convert to milliseconds

            # Ghi vào file log bao gồm latency
            status = "SUCCESS" if total_bytes == filesize else "INCOMPLETE"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{safe_filename},{total_bytes},{duration:.2f},{status},{latency:.2f}\n")

            if status == "SUCCESS":
                client_socket.sendall(b"UPLOAD_SUCCESS")
                self.log_message(f"File '{safe_filename}' ({total_bytes} bytes) received in {duration:.2f} seconds. Latency: {latency:.2f} ms")
                self.total_transfers += 1
            else:
                client_socket.sendall(b"UPLOAD_INCOMPLETE")
                self.log_message(f"File '{safe_filename}' incomplete. Received {total_bytes} of {filesize} bytes. Latency: {latency:.2f} ms")
                self.failed_transfers += 1

            self.transfer_speed_label.config(text=f"Transfer Performance: {transfer_speed:.2f} bytes/sec", fg="blue")
            self.update_file_list()
            self.master.after(0, self.update_graphs)

        except Exception as e:
            client_socket.sendall(b"ERROR: File transfer failed.")
            self.log_message(f"Failed to save file '{filename}': {e}")
            self.failed_transfers += 1
            self.update_packet_loss_rate()
            self.master.after(0, self.update_graphs)

            

    def handle_list(self, client_socket):
        try:
            files = os.listdir(self.received_files_path)
            file_list = "|".join(files)
            client_socket.sendall(file_list.encode("utf-8"))
        except Exception as e:
            client_socket.sendall(b"ERROR: Unable to list files.")
            self.log_message(f"Error listing files: {e}")

    def handle_download(self, client_socket, request, client_address):
        try:
            parts = request.strip().split(" ", 1)
            if len(parts) < 2:
                client_socket.sendall(b"ERROR: Invalid DOWNLOAD command.\n")
                return

            _, filename = parts
            filepath = os.path.join(self.received_files_path, os.path.basename(filename))

            if os.path.exists(filepath):
                filesize = os.path.getsize(filepath)
                response = f"FILE_FOUND {filesize}\n"
                client_socket.sendall(response.encode("utf-8"))  # Đảm bảo kết thúc bằng '\n'

                # Gửi dữ liệu file
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        client_socket.sendall(chunk)
            else:
                response = "FILE_NOT_FOUND\n"
                client_socket.sendall(response.encode("utf-8"))  # Đảm bảo kết thúc bằng '\n'
        except Exception as e:
            error_message = "ERROR: Unable to send file.\n"
            client_socket.sendall(error_message.encode("utf-8"))
            logging.error(f"Error handling download: {e}")

    def handle_delete(self, client_socket, request):
        try:
            parts = request.split(" ", 1)
            if len(parts) < 2:
                client_socket.sendall(b"ERROR: Invalid DELETE command.")
                return

            _, filename = parts
            filepath = os.path.join(self.received_files_path, os.path.basename(filename))

            if os.path.exists(filepath):
                os.remove(filepath)
                client_socket.sendall(b"FILE_DELETED")
                self.log_message(f"File '{filename}' deleted by client.")
                self.update_file_list()
            else:
                client_socket.sendall(b"FILE_NOT_FOUND")
        except Exception as e:
            client_socket.sendall(b"ERROR: Unable to delete file.")
            self.log_message(f"Error deleting file '{filename}': {e}")

    def update_file_list(self):
        self.files_listbox.delete(0, tk.END)
        try:
            files = os.listdir(self.received_files_path)
            for file in files:
                self.files_listbox.insert(tk.END, file)
        except Exception as e:
            self.log_message(f"Error updating file list: {e}")

    def delete_file(self):
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No file selected.")
            return

        filename = self.files_listbox.get(selection[0])
        filepath = os.path.join(self.received_files_path, filename)

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                self.log_message(f"File '{filename}' deleted by server.")
                self.update_file_list()
                messagebox.showinfo("Success", f"File '{filename}' deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {e}")
        else:
            messagebox.showerror("Error", "File not found.")

    def open_file(self, event):
        selection = self.files_listbox.curselection()
        if not selection:
            return
        filename = self.files_listbox.get(selection[0])
        filepath = os.path.join(self.received_files_path, filename)

        # Mở file dựa trên loại
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            self.display_image(filepath)
        elif filename.lower().endswith(('.txt', '.csv', '.log')):
            self.display_text(filepath)
        else:
            try:
                os.startfile(filepath)
            except AttributeError:
                # Cho các hệ điều hành không phải Windows
                import subprocess
                subprocess.call(['open' if os.name == 'posix' else 'xdg-open', filepath])
            except Exception as e:
                messagebox.showerror("Error", f"Unable to open file: {e}")

    def display_image(self, filepath):
        try:
            img_window = tk.Toplevel(self.master)
            img_window.title(f"Viewing: {os.path.basename(filepath)}")
            img = Image.open(filepath)
            img.thumbnail((800, 800))  # Điều chỉnh kích thước nếu cần
            img_tk = ImageTk.PhotoImage(img)
            label = tk.Label(img_window, image=img_tk)
            label.image = img_tk
            label.pack()
        except Exception as e:
            messagebox.showerror("Error", f"Unable to display image: {e}")

    def display_text(self, filepath):
        try:
            text_window = tk.Toplevel(self.master)
            text_window.title(f"Viewing: {os.path.basename(filepath)}")
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            text_area = scrolledtext.ScrolledText(
                text_window,
                wrap=tk.WORD,
                width=100,
                height=30,
                font=("Arial", 10)
            )
            text_area.insert(tk.END, content)
            text_area.config(state=tk.DISABLED)
            text_area.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to display text: {e}")

    def update_graphs(self):
        # Xóa các biểu đồ hiện tại
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        try:
            # Đọc và xử lý dữ liệu từ tệp log
            with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
                df = pd.read_csv(f)

            # Kiểm tra các cột cần thiết
            required_columns = {"Filename", "FileSize", "Duration", "Status", "Latency"}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                self.log_message(f"Missing columns in log file: {', '.join(missing)}")
                return

            # Lọc các dòng hợp lệ
            df = df[(df["Duration"] > 0) & (df["FileSize"] > 0)]
            df["Speed"] = df["FileSize"] / df["Duration"]

            # Tạo một khung phụ để quản lý layout
            graphs_subframe = tk.Frame(self.graph_frame)
            graphs_subframe.pack(fill=tk.BOTH, expand=True)

            # 1. Bandwidth Over Time
            fig_bandwidth, ax_bandwidth = plt.subplots(figsize=(5, 4))
            ax_bandwidth.plot(df.index + 1, df["Speed"], marker='o', linestyle='-', color='blue')
            ax_bandwidth.set_title("Transmission speed")
            ax_bandwidth.set_xlabel("Transfer Number")
            ax_bandwidth.set_ylabel("Speed (bytes/second)")
            ax_bandwidth.grid(True)
            canvas_bandwidth = FigureCanvasTkAgg(fig_bandwidth, master=graphs_subframe)
            canvas_bandwidth.draw()
            canvas_bandwidth.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

           

            # 3. File Size vs Transfer Time
            fig_file_size_time, ax_file_size_time = plt.subplots(figsize=(5, 4))
            ax_file_size_time.scatter(df["FileSize"], df["Duration"], color='green')
            ax_file_size_time.set_title("File Size vs. Transfer Time")
            ax_file_size_time.set_xlabel("File Size (bytes)")
            ax_file_size_time.set_ylabel("Transfer Time (seconds)")
            ax_file_size_time.grid(True)
            canvas_file_size_time = FigureCanvasTkAgg(fig_file_size_time, master=graphs_subframe)
            canvas_file_size_time.draw()
            canvas_file_size_time.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            # 4. Latency Over Transfers
            fig_latency, ax_latency = plt.subplots(figsize=(5, 4))
            ax_latency.plot(df.index + 1, df["Latency"], marker='o', linestyle='-', color='purple')
            ax_latency.set_title("Latency Over Transfers")
            ax_latency.set_xlabel("Transfer Number")
            ax_latency.set_ylabel("Latency (ms)")
            ax_latency.grid(True)
            canvas_latency = FigureCanvasTkAgg(fig_latency, master=graphs_subframe)
            canvas_latency.draw()
            canvas_latency.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        except pd.errors.EmptyDataError:
            self.log_message("Log file is empty. No data to display.")
        except pd.errors.ParserError as e:
            self.log_message(f"Error parsing log file: {e}")
        except KeyError as e:
            self.log_message(f"Missing expected column in log file: {e}")
        except Exception as e:
            self.log_message(f"Error updating graphs: {e}")

    
    def on_closing(self):
        if self.running:
            self.stop_server()
        self.master.destroy()

    # Optional: Implement periodic graph updates
    """
    def start_graph_refresh(self):
        self.update_graphs()
        # Schedule the next update after 60 seconds (60000 milliseconds)
        self.master.after(60000, self.start_graph_refresh)
    """

def main():
    root = tk.Tk()
    app = FileServerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
