using Unity.Netcode;
using Unity.Netcode.Transports.UTP;
using UnityEngine;

namespace CloudBuildTest
{
    public class ServerManager : MonoBehaviour
    {
#if UNITY_SERVER
        private void Start()
        {
            var transport = NetworkManager.Singleton.GetComponent<UnityTransport>();
            ushort port = transport != null ? transport.ConnectionData.Port : (ushort)7777;

            NetworkManager.Singleton.StartServer();
            Debug.Log($"Server Started on Port {port}");
        }
#endif
    }
}
