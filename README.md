# Smart Data Management Android Port

## Overview  
Smart Data Management Android Port is a cross-platform mobile solution designed to securely store and retrieve complete student reports through NFC technology. By combining encryption, compression, and efficient data handling, the project ensures seamless access to academic data within strict storage constraints.

This work was carried out as part of an internship, focusing on solving real-world constraints in academic data portability and security.

## Key Contributions  
- **NFC Data Optimization**  
  - Implemented encryption and compression algorithms to fit full student reports within an 8KB NFC payload.  
  - Achieved **100% reliable cross-platform access** across supported Android devices.  

- **Cross-Platform Integration**  
  - Developed a **React Native Android app** with a **custom `NFC` module** for low-level NFC operations.  
  - Delivered a smooth and user-friendly interface for reading and writing encrypted student data.  

- **Security & Reliability**  
  - Ensured encrypted data transmission and storage.  
  - Validated compatibility across multiple Android versions with consistent performance.  

- **Data Management & API Handling**  
  - Used **Zod** for runtime input validation and schema enforcement.  
  - Integrated **Axios** for reliable API requests with token handling and error recovery.  
  - Adopted **React Query** for declarative data fetching, caching, and background sync.  
  - Leveraged **Protocol Buffers (protobuf)** for compact, strongly typed, and efficient data serialization.  

## Tech Stack  
- **TypeScript** – Core application logic and data handling  
- **React Native** – Cross-platform mobile app development  
- **NFC (Android)** – Secure data transfer and storage  
- **Zod** – Input validation and schema management  
- **Axios** – API communication and error handling  
- **React Query** – Data fetching, caching, and synchronization  
- **Protocol Buffers (protobuf)** – Compact data serialization  


## How to connect PC to mobile
  - adb devices
  - adb reverse tcp:8000 tcp:8000 // Android -> PC:8000
  - Access the site from android