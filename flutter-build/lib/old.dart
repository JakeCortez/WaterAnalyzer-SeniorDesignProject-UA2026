import 'package:flutter/material.dart';
import 'piserver.dart';

void main() => runApp(MaterialApp(home: PiControlPage()));

class PiControlPage extends StatefulWidget {
  @override
  _PiControlPageState createState() => _PiControlPageState();
}

class _PiControlPageState extends State<PiControlPage> {
  String status = "Idle";
  final PiService pi = PiService();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Pi Controller")),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text("Status: $status", textAlign: TextAlign.center),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: () async {
                String res = await pi.sendCommand("START_ANALYSIS");
                setState(() => status = res);
              },
              child: Text("Send Command"),
            ),
            ElevatedButton(
              onPressed: () async {
                setState(() => status = "Downloading...");
                String res = await pi.downloadFile();
                setState(() => status = res);
              },
              child: Text("Receive File"),
            ),
          ],
        ),
      ),
    );
  }
}

