package com.example.voxshield

import android.content.Context
import org.webrtc.*

class WebRTCClient(
    context: Context,
    private val observer: PeerConnection.Observer
) {

    private val eglBaseContext = EglBase.create().eglBaseContext
    private val peerConnectionFactory: PeerConnectionFactory

    var peerConnection: PeerConnection? = null
    private var localAudioTrack: AudioTrack? = null
    private var audioSource: AudioSource? = null

    init {
        PeerConnectionFactory.initialize(
            PeerConnectionFactory.InitializationOptions.builder(context)
                .setEnableInternalTracer(true)
                .createInitializationOptions()
        )

        val audioDeviceModule = org.webrtc.audio.JavaAudioDeviceModule.builder(context)
            .setUseHardwareAcousticEchoCanceler(true)
            .setUseHardwareNoiseSuppressor(true)
            .createAudioDeviceModule()

        val options = PeerConnectionFactory.Options()
        peerConnectionFactory = PeerConnectionFactory.builder()
            .setOptions(options)
            .setAudioDeviceModule(audioDeviceModule)
            .createPeerConnectionFactory()
    }

    fun startLocalAudio(context: Context) {
        val audioConstraints = MediaConstraints()
        audioSource = peerConnectionFactory.createAudioSource(audioConstraints)
        localAudioTrack = peerConnectionFactory.createAudioTrack("101", audioSource)
        localAudioTrack?.setEnabled(true)
    }

    fun initializePeerConnection() {
        val iceServers = listOf(
            PeerConnection.IceServer.builder("stun:stun.l.google.com:19302").createIceServer()
        )

        peerConnection = peerConnectionFactory.createPeerConnection(iceServers, observer)
        
        localAudioTrack?.let {
            peerConnection?.addTrack(it, listOf("stream_1"))
        }
    }

    fun createOffer(sdpObserver: SdpObserver) {
        val constraints = MediaConstraints()
        peerConnection?.createOffer(sdpObserver, constraints)
    }

    fun createAnswer(sdpObserver: SdpObserver) {
        val constraints = MediaConstraints()
        peerConnection?.createAnswer(sdpObserver, constraints)
    }

    fun setLocalDescription(observer: SdpObserver, sdp: SessionDescription) {
        peerConnection?.setLocalDescription(observer, sdp)
    }

    fun setRemoteDescription(observer: SdpObserver, sdp: SessionDescription) {
        peerConnection?.setRemoteDescription(observer, sdp)
    }

    fun addIceCandidate(candidate: IceCandidate) {
        peerConnection?.addIceCandidate(candidate)
    }

    fun destroy() {
        peerConnection?.close()
        audioSource?.dispose()
        peerConnectionFactory.dispose()
    }
}
