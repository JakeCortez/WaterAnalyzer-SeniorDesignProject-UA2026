import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

void main() => runApp(MaterialApp(
  theme: ThemeData(primarySwatch: Colors.blueGrey),
  home: PiControlPage(),
));

class PiControlPage extends StatefulWidget {
  @override
  _PiControlPageState createState() => _PiControlPageState();
}

class _PiControlPageState extends State<PiControlPage> {
  String status = "Ready";
  final int port = 65432;

  // 1. Controller to handle IP input
  final TextEditingController _ipController = TextEditingController(text: "192.168.2.137");

  // Helper to get current IP from controller
  String get piIp => _ipController.text.trim();

  void logToUI(String message) {
    final now = DateTime.now();
    final ts = "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}:${now.second.toString().padLeft(2, '0')}";
    setState(() {
      status = "[$ts] $message";
    });
  }

  Future<void> sendCommand(String command) async {
    try {
      logToUI("Connecting to $piIp...");
      Socket socket = await Socket.connect(piIp, port, timeout: Duration(seconds: 5));
      socket.write(command);
      
      Uint8List response = await socket.first;
      logToUI("Server: ${String.fromCharCodes(response)}");
      socket.destroy();
    } catch (e) {
      logToUI("Error: $e");
    }
  }

  Future<void> downloadFile() async {
    var permission = await Permission.storage.request();
    if (!permission.isGranted) {
      logToUI("Permission Denied");
      return;
    }

    try {
      logToUI("Connecting to $piIp for file...");
      Socket socket = await Socket.connect(piIp, port, timeout: Duration(seconds: 5));

      socket.write("Download");

      final now = DateTime.now();
      final timestamp = "${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}_"
                        "${now.hour.toString().padLeft(2, '0')}${now.minute.toString().padLeft(2, '0')}${now.second.toString().padLeft(2, '0')}";

      String path = '/storage/emulated/0/Download';
      String fileName = 'analysis_results_$timestamp.png';
      final file = File('$path/$fileName');

      if (await file.exists()) await file.delete();

      await socket.forEach((data) {
        file.writeAsBytesSync(data, mode: FileMode.append);
      });

      logToUI("Saved to: Downloads/$fileName");
      socket.destroy();
    } catch (e) {
      logToUI("Download Error: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Instant Raman Water Analyzer")),
      body: SingleChildScrollView( // Added to prevent overflow when keyboard appears
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            // --- NEW IP ADDRESS INPUT BOX ---
            Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: TextField(
                  controller: _ipController,
                  decoration: InputDecoration(
                    labelText: "Analyzer IP Address",
                    hintText: "e.g. 192.168.1.50",
                    prefixIcon: Icon(Icons.lan),
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.numberWithOptions(decimal: true),
                ),
              ),
            ),
            // --------------------------------
            
            SizedBox(height: 20),
            
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(15),
              decoration: BoxDecoration(color: Colors.grey[200], borderRadius: BorderRadius.circular(8)),
              child: Text(status, style: TextStyle(fontFamily: 'monospace')),
            ),
            
            SizedBox(height: 30),
            
            ElevatedButton(
              style: ElevatedButton.styleFrom(minimumSize: Size(double.infinity, 50)),
              onPressed: () => sendCommand("Start_Analysis"),
              child: Text("Start Analysis"),
            ),
            
            SizedBox(height: 20),
            
            ElevatedButton.icon(
              icon: Icon(Icons.download),
              label: Text("Download Detailed Report"),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blueGrey[700],
                foregroundColor: Colors.white,
                minimumSize: Size(double.infinity, 50)
              ),
              onPressed: downloadFile,
            ),
          ],
        ),
      ),
    );
  }
}