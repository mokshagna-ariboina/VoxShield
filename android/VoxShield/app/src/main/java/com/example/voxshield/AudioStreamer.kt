package com.example.voxshield

import android.util.Log
import okhttp3.*
import okio.ByteString.Companion.toByteString
import org.webrtc.AudioTrackSink
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.util.concurrent.Executors

class AudioStreamer : AudioTrackSink, WebSocketListener() {

    private val client = OkHttpClient()
    private var webSocket: WebSocket? = null
    private val buffer = ByteArrayOutputStream()
    private val executor = Executors.newSingleThreadExecutor()

    fun start() {
        val request = Request.Builder().url(Config.ANALYSIS_SERVER_URL).build()
        webSocket = client.newWebSocket(request, this)
        Log.d("AudioStreamer", "Connecting to analysis server: ${Config.ANALYSIS_SERVER_URL}")
    }

    fun stop() {
        webSocket?.close(1000, "Call ended")
        executor.shutdown()
        Log.d("AudioStreamer", "Stopped analysis stream")
    }

    override fun onData(
        audioData: ByteBuffer,
        bitsPerSample: Int,
        sampleRate: Int,
        numberOfChannels: Int,
        numberOfFrames: Int,
        absoluteCaptureTimestampMs: Long
    ) {
        // Read raw PCM bytes from ByteBuffer
        val rawBytes = ByteArray(audioData.remaining())
        audioData.get(rawBytes)

        executor.execute {
            try {
                // Normalize to 16kHz Mono 16-bit PCM
                val normalizedBytes = normalizeTo16kHzMono(rawBytes, sampleRate, numberOfChannels, numberOfFrames)
                buffer.write(normalizedBytes)

                // Send every ~500ms of 16kHz mono (16000 samples/sec * 2 bytes = 32000 bytes/sec -> 16000 bytes/500ms)
                if (buffer.size() >= 16000) {
                    val chunk = buffer.toByteArray()
                    buffer.reset()
                    webSocket?.send(chunk.toByteString())
                    Log.d("AudioStreamer", "Sent ${chunk.size} bytes of normalized audio")
                }
            } catch (e: Exception) {
                Log.e("AudioStreamer", "Error processing audio frame", e)
            }
        }
    }

    private fun normalizeTo16kHzMono(
        inputBytes: ByteArray,
        inputSampleRate: Int,
        inputChannels: Int,
        numFrames: Int
    ): ByteArray {
        if (inputSampleRate == 16000 && inputChannels == 1) {
            return inputBytes
        }

        val ratio = inputSampleRate / 16000.0f
        val outFrames = (numFrames / ratio).toInt()
        val outputBytes = ByteArray(outFrames * 2)

        for (i in 0 until outFrames) {
            val inIndex = (i * ratio).toInt()
            if (inIndex >= numFrames) break

            var sum = 0
            for (c in 0 until inputChannels) {
                val byteIndex = (inIndex * inputChannels + c) * 2
                if (byteIndex + 1 < inputBytes.size) {
                    val low = inputBytes[byteIndex].toInt() and 0xFF
                    val high = inputBytes[byteIndex + 1].toInt() shl 8
                    val sample = (low or high).toShort().toInt()
                    sum += sample
                }
            }

            val mixed = (sum / inputChannels).toShort()
            val outByteIndex = i * 2
            if (outByteIndex + 1 < outputBytes.size) {
                outputBytes[outByteIndex] = (mixed.toInt() and 0xFF).toByte()
                outputBytes[outByteIndex + 1] = ((mixed.toInt() shr 8) and 0xFF).toByte()
            }
        }
        return outputBytes
    }

    override fun onOpen(webSocket: WebSocket, response: Response) {
        Log.d("AudioStreamer", "Connected to analysis server")
    }

    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
        Log.e("AudioStreamer", "Analysis server connection failed", t)
        // Failure shouldn't crash the app, call continues normally
    }
}
