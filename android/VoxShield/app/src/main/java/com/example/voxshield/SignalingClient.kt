package com.example.voxshield

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonObject
import okhttp3.*
import org.webrtc.IceCandidate
import org.webrtc.SessionDescription

class SignalingClient(
    private val myId: String,
    private val listener: SignalingListener
) : WebSocketListener() {

    private val client = OkHttpClient()
    private var webSocket: WebSocket? = null
    private val gson = Gson()

    fun connect() {
        val request = Request.Builder().url(Config.SIGNALING_SERVER_URL).build()
        webSocket = client.newWebSocket(request, this)
    }

    override fun onOpen(webSocket: WebSocket, response: Response) {
        Log.d("SignalingClient", "Connected to signaling server")
        val registerMsg = JsonObject().apply {
            addProperty("type", "register")
            addProperty("id", myId)
        }
        webSocket.send(registerMsg.toString())
    }

    override fun onMessage(webSocket: WebSocket, text: String) {
        Log.d("SignalingClient", "Received: $text")
        val json = gson.fromJson(text, JsonObject::class.java)
        val type = json.get("type").asString
        val sender = json.get("sender").asString
        val payload = json.getAsJsonObject("payload")

        when (type) {
            "offer" -> {
                val sdp = SessionDescription(SessionDescription.Type.OFFER, payload.get("sdp").asString)
                listener.onOfferReceived(sdp, sender)
            }
            "answer" -> {
                val sdp = SessionDescription(SessionDescription.Type.ANSWER, payload.get("sdp").asString)
                listener.onAnswerReceived(sdp)
            }
            "ice_candidate" -> {
                val candidate = IceCandidate(
                    payload.get("sdpMid").asString,
                    payload.get("sdpMLineIndex").asInt,
                    payload.get("candidate").asString
                )
                listener.onIceCandidateReceived(candidate)
            }
        }
    }

    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
        Log.e("SignalingClient", "Error: $t")
    }

    fun sendOffer(target: String, sdp: SessionDescription) {
        val payload = JsonObject().apply {
            addProperty("type", sdp.type.canonicalForm())
            addProperty("sdp", sdp.description)
        }
        sendMessage("offer", target, payload)
    }

    fun sendAnswer(target: String, sdp: SessionDescription) {
        val payload = JsonObject().apply {
            addProperty("type", sdp.type.canonicalForm())
            addProperty("sdp", sdp.description)
        }
        sendMessage("answer", target, payload)
    }

    fun sendIceCandidate(target: String, candidate: IceCandidate) {
        val payload = JsonObject().apply {
            addProperty("sdpMid", candidate.sdpMid)
            addProperty("sdpMLineIndex", candidate.sdpMLineIndex)
            addProperty("candidate", candidate.sdp)
        }
        sendMessage("ice_candidate", target, payload)
    }

    private fun sendMessage(type: String, target: String, payload: JsonObject) {
        val msg = JsonObject().apply {
            addProperty("type", type)
            addProperty("target", target)
            add("payload", payload)
        }
        webSocket?.send(msg.toString())
    }

    fun destroy() {
        webSocket?.close(1000, "App destroyed")
        client.dispatcher.executorService.shutdown()
    }

    interface SignalingListener {
        fun onOfferReceived(sdp: SessionDescription, sender: String)
        fun onAnswerReceived(sdp: SessionDescription)
        fun onIceCandidateReceived(candidate: IceCandidate)
    }
}
