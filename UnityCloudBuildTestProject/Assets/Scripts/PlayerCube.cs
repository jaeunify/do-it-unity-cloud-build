using Unity.Netcode;
using Unity.Netcode.Components;
using UnityEngine;

namespace CloudBuildTest
{
    [RequireComponent(typeof(NetworkObject))]
    [RequireComponent(typeof(NetworkTransform))]
    public class PlayerCube : NetworkBehaviour
    {
        private const float MoveSpeed = 5f;

        public override void OnNetworkSpawn()
        {
            if (!IsServer) return;

            transform.position = new Vector3(
                Random.Range(-5f, 5f),
                0.5f,
                Random.Range(-5f, 5f));
        }

        private void Update()
        {
            if (!IsOwner) return;

            float h = Input.GetAxis("Horizontal");
            float v = Input.GetAxis("Vertical");
            if (h == 0f && v == 0f) return;

            // 클라이언트에서 delta 계산 후 서버에 전달 → NetworkTransform이 전파
            MoveServerRpc(new Vector3(h, 0f, v) * (MoveSpeed * Time.deltaTime));
        }

        [ServerRpc]
        private void MoveServerRpc(Vector3 delta)
        {
            transform.position += delta;
        }
    }
}
