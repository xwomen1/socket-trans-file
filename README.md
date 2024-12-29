# File Sharing Client-Server Application

![Project Logo](https://via.placeholder.com/150)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Running the Server](#running-the-server)
  - [Running the Client](#running-the-client)
- [Logging](#logging)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Overview

The **File Sharing Client-Server Application** is a Python-based solution that enables users to upload and download files between a client and a server over a network. The client features a user-friendly graphical interface built with Tkinter, providing functionalities such as connecting to the server, uploading files, listing available files on the server, and downloading selected files with real-time progress indicators.

## Features

- **Connect to Server:** Establish a connection to the file server using IP and port.
- **Disconnect:** Safely terminate the connection to the server.
- **Upload Files:** Select and upload files from the local system to the server with progress tracking.
- **List Files:** Retrieve and display a list of available files on the server.
- **Download Files:** Select and download files from the server to the local system with progress tracking.
- **Progress Bars:** Visual indicators for upload and download processes.
- **Logging:** Comprehensive logging of client activities and errors.
- **Error Handling:** Informative messages and logs for various error scenarios.

## Architecture

The application follows a client-server architecture:

- **Server:** Handles incoming connections, processes upload and download requests, and manages file storage.
- **Client:** Provides a graphical user interface for users to interact with the server, facilitating file uploads and downloads.

![Architecture Diagram](https://via.placeholder.com/600x400)

> **Lưu ý:** Bạn nên thêm hình ảnh lưu đồ kiến trúc thực tế của dự án vào đường dẫn ảnh trên hoặc cập nhật liên kết với hình ảnh phù hợp.

## Prerequisites

- **Python 3.7+**
- **Required Python Libraries:**
  - `tkinter` (thường đi kèm với Python)
  - `socket`
  - `threading`
  - `logging`
  - `os`

> **Lưu ý:** Phần server có thể yêu cầu thêm các thư viện tùy thuộc vào cách triển khai cụ thể.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/file-sharing-app.git
   cd file-sharing-app
