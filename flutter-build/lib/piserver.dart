import 'dart:io';
import 'dart:typed_data';
import 'package:path_provider/path_provider.dart';
//---------------THIS PAGE IS DEPRECIATED AND NOT IN USE---------------------//
class PiService {
  final String ip = "192.168.2.137";
  final int port = 65432;

  // Send a simple text command
  Future<String> sendCommand(String command) async {
    try {
      Socket socket = await Socket.connect(ip, port);
      socket.write(command);
      
      // Wait for server response
      Uint8List response = await socket.first;
      socket.destroy();
      return String.fromCharCodes(response);
    } catch (e) {
      return "Error: $e";
    }
  }

  

  // Receive a file from the Pi
  Future<String> downloadFile() async {
    try {
      Socket socket = await Socket.connect(ip, port);
      socket.write("GET_FILE");

      // Get path to save file
      final directory = await getExternalStorageDirectory();
      final file = File('${directory!.path}/analysis_results.txt');

      // Sink the socket stream into the file
      await socket.forEach((data) {
        file.writeAsBytesSync(data, mode: FileMode.append);
      });

      socket.destroy();
      return "File saved to: ${file.path}";
    } catch (e) {
      return "Download failed: $e";
    }
  }
}