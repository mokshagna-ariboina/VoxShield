package com.example.voxshield

import android.util.Log
import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import org.webrtc.*

class MainActivity : ComponentActivity(), SignalingClient.SignalingListener, PeerConnection.Observer {

    private lateinit var webRTCClient: WebRTCClient
    private lateinit var signalingClient: SignalingClient
    private lateinit var audioStreamer: AudioStreamer

    private var targetId by mutableStateOf("")
    private var myId by mutableStateOf((1000..9999).random().toString())
    private var callStatus by mutableStateOf("Disconnected")

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            initWebRTC()
        } else {
            Toast.makeText(this, "Audio permission is required", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text("My ID: $myId", style = MaterialTheme.typography.headlineSmall)
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        OutlinedTextField(
                            value = targetId,
                            onValueChange = { targetId = it },
                            label = { Text("Call To ID") }
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        Button(onClick = { initiateCall() }) {
                            Text("Call")
                        }
                        
                        Spacer(modifier = Modifier.height(32.dp))
                        Text("Status: $callStatus", style = MaterialTheme.typography.bodyLarge)
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { endCall() }, colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)) {
                            Text("End Call")
                        }
                    }
                }
            }
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
            initWebRTC()
        } else {
            requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    private fun initWebRTC() {
        webRTCClient = WebRTCClient(this, this)
        webRTCClient.startLocalAudio(this)

        signalingClient = SignalingClient(myId, this)
        signalingClient.connect()
        
        audioStreamer = AudioStreamer()
        audioStreamer.start()
        
        callStatus = "Connected to Signaling"
    }

    private fun initiateCall() {
        if (targetId.isEmpty()) return
        callStatus = "Calling $targetId..."
        
        webRTCClient.initializePeerConnection()
        webRTCClient.createOffer(object : SdpObserver {
            override fun onCreateSuccess(sdp: SessionDescription) {
                webRTCClient.setLocalDescription(this, sdp)
                signalingClient.sendOffer(targetId, sdp)
            }
            override fun onSetSuccess() {}
            override fun onCreateFailure(e: String?) {}
            override fun onSetFailure(e: String?) {}
        })
    }

    override fun onOfferReceived(sdp: SessionDescription, sender: String) {
        runOnUiThread {
            callStatus = "Incoming call from $sender"
            targetId = sender
            
            webRTCClient.initializePeerConnection()
            webRTCClient.setRemoteDescription(object : SdpObserver {
                override fun onCreateSuccess(sdp: SessionDescription?) {}
                override fun onSetSuccess() {
                    webRTCClient.createAnswer(object : SdpObserver {
                        override fun onCreateSuccess(answerSdp: SessionDescription) {
                            webRTCClient.setLocalDescription(this, answerSdp)
                            signalingClient.sendAnswer(sender, answerSdp)
                            runOnUiThread { callStatus = "In Call with $sender" }
                        }
                        override fun onSetSuccess() {}
                        override fun onCreateFailure(e: String?) {}
                        override fun onSetFailure(e: String?) {}
                    })
                }
                override fun onCreateFailure(e: String?) {}
                override fun onSetFailure(e: String?) {}
            }, sdp)
        }
    }

    override fun onAnswerReceived(sdp: SessionDescription) {
        runOnUiThread {
            webRTCClient.setRemoteDescription(object : SdpObserver {
                override fun onCreateSuccess(sdp: SessionDescription?) {}
                override fun onSetSuccess() {
                    runOnUiThread { callStatus = "In Call with $targetId" }
                }
                override fun onCreateFailure(e: String?) {}
                override fun onSetFailure(e: String?) {}
            }, sdp)
        }
    }

    override fun onIceCandidateReceived(candidate: IceCandidate) {
        webRTCClient.addIceCandidate(candidate)
    }

    private fun endCall() {
        webRTCClient.peerConnection?.close()
        webRTCClient.peerConnection = null
        callStatus = "Call Ended"
    }

    override fun onDestroy() {
        super.onDestroy()
        signalingClient.destroy()
        webRTCClient.destroy()
        audioStreamer.stop()
    }

    // PeerConnection.Observer methods
    override fun onIceCandidate(candidate: IceCandidate) {
        signalingClient.sendIceCandidate(targetId, candidate)
    }

    override fun onSignalingChange(newState: PeerConnection.SignalingState?) {}
    override fun onIceConnectionChange(newState: PeerConnection.IceConnectionState?) {}
    override fun onIceConnectionReceivingChange(receiving: Boolean) {}
    override fun onIceGatheringChange(newState: PeerConnection.IceGatheringState?) {}
    override fun onIceCandidatesRemoved(candidates: Array<out IceCandidate>?) {}
    
    override fun onAddStream(stream: MediaStream?) {}
    override fun onRemoveStream(stream: MediaStream?) {}
    override fun onDataChannel(dataChannel: DataChannel?) {}
    override fun onRenegotiationNeeded() {}
    
    override fun onAddTrack(receiver: RtpReceiver?, mediaStreams: Array<out MediaStream>?) {
        val track = receiver?.track()
        if (track is AudioTrack) {
            track.addSink(audioStreamer)
            Log.d("MainActivity", "Attached AudioStreamer to remote AudioTrack")
        }
    }
}
