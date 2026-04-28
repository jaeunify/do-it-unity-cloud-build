using Unity.Netcode;
using UnityEngine;

namespace CloudBuildTest
{
    public class AutoConnect : MonoBehaviour
    {
#if !UNITY_SERVER
        private void Start()
        {
            NetworkManager.Singleton.StartClient();
        }
#endif
    }
}
