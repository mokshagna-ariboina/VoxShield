import org.webrtc.AudioTrack
fun test(track: AudioTrack) {
    val methods = track.javaClass.methods
    for (m in methods) {
        if (m.name.contains("Sink")) {
            println(m.name)
        }
    }
}
