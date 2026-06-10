module.exports = ({ env }) => {
  const wantsCloudinary = env('UPLOAD_PROVIDER', 'local') === 'cloudinary';
  const hasCloudinaryConfig = Boolean(
    env('CLOUDINARY_NAME') &&
    env('CLOUDINARY_KEY') &&
    env('CLOUDINARY_SECRET')
  );
  const useCloudinary = wantsCloudinary && hasCloudinaryConfig;

  return {
    upload: {
      config: {
        provider: useCloudinary ? 'cloudinary' : 'local',
        providerOptions: useCloudinary
          ? {
              cloud_name: env('CLOUDINARY_NAME'),
              api_key: env('CLOUDINARY_KEY'),
              api_secret: env('CLOUDINARY_SECRET'),
            }
          : {},
        actionOptions: {
          upload: {},
          uploadStream: {},
          delete: {},
        },
      },
    },
  };
};
